"""Duplicate detection.

A new report joins an existing incident only when all three hold:
  semantic  cosine similarity of embeddings >= tau
  spatial   locations within radius r (skipped if either side has no location)
  temporal  incident last updated within window dt
"""

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from ..config import Settings, get_settings
from ..models import Incident


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def find_matching_incident(
    candidates: list[Incident],
    embedding: list[float],
    lat: float | None,
    lon: float | None,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> Incident | None:
    """Return the best-matching open incident, or None if this is a new incident."""
    s = settings or get_settings()
    now = now or datetime.now(timezone.utc)
    window = timedelta(hours=s.dedup_window_hours)

    best: tuple[float, Incident] | None = None
    for inc in candidates:
        if inc.status == "resolved" or inc.centroid is None:
            continue
        if now - _aware(inc.updated_at) > window:
            continue
        if None not in (lat, lon, inc.lat, inc.lon):
            if haversine_km(lat, lon, inc.lat, inc.lon) > s.dedup_radius_km:
                continue
        sim = cosine(embedding, inc.centroid)
        if sim < s.dedup_similarity:
            continue
        if best is None or sim > best[0]:
            best = (sim, inc)
    return best[1] if best else None


def update_centroid(centroid: list[float] | None, n_existing: int, new: list[float]) -> list[float]:
    """Running mean of report embeddings."""
    if centroid is None or n_existing <= 0:
        return list(new)
    c = np.asarray(centroid, dtype=float)
    v = np.asarray(new, dtype=float)
    return ((c * n_existing + v) / (n_existing + 1)).tolist()
