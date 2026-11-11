"""Severity scoring.

    S(c) = 100 * (0.40 L + 0.20 U + 0.15 P + 0.15 V + 0.10 A)

L life threat, U urgency, P people affected (log-scaled), V verification, A isolation.
Every factor is normalised to [0, 1]. Weights are initial proposals, to be calibrated with
district disaster-management officers and later with logged responder overrides.
"""

import math
from dataclasses import dataclass

from ..config import Settings, get_settings

WEIGHTS = {"L": 0.40, "U": 0.20, "P": 0.15, "V": 0.15, "A": 0.10}
LIFE_ESCALATION_THRESHOLD = 0.8
PEOPLE_CAP = 50  # people count at which the P factor saturates at 1.0
VERIFICATION_CAP = 4  # independent reports at which V saturates at 1.0

TIER_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class Factors:
    life: float = 0.0
    urgency: float = 0.0
    people: float = 0.0
    verification: float = 0.0
    isolation: float = 0.0


def people_factor(count: int) -> float:
    """Log-scaled so 1 -> 3 people matters more than 40 -> 50."""
    if count <= 0:
        return 0.0
    return min(1.0, math.log1p(count) / math.log1p(PEOPLE_CAP))


def verification_factor(report_count: int) -> float:
    """First report carries no corroboration; each independent report adds confidence."""
    if report_count <= 1:
        return 0.0
    return min(1.0, (report_count - 1) / (VERIFICATION_CAP - 1))


def compute_score(f: Factors) -> float:
    raw = (
        WEIGHTS["L"] * f.life
        + WEIGHTS["U"] * f.urgency
        + WEIGHTS["P"] * f.people
        + WEIGHTS["V"] * f.verification
        + WEIGHTS["A"] * f.isolation
    )
    return round(100.0 * max(0.0, min(1.0, raw)), 1)


def tier_for(score: float, life: float, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    if life > LIFE_ESCALATION_THRESHOLD:
        return "CRITICAL"
    if score >= s.tier_critical:
        return "CRITICAL"
    if score >= s.tier_high:
        return "HIGH"
    if score >= s.tier_medium:
        return "MEDIUM"
    return "LOW"


def score_incident(f: Factors, settings: Settings | None = None) -> tuple[float, str]:
    score = compute_score(f)
    return score, tier_for(score, f.life, settings)
