from app.services.scoring import (
    Factors,
    compute_score,
    people_factor,
    score_incident,
    tier_for,
    verification_factor,
)


def test_formula_matches_poster():
    f = Factors(life=1.0, urgency=1.0, people=1.0, verification=1.0, isolation=1.0)
    assert compute_score(f) == 100.0
    assert compute_score(Factors()) == 0.0
    # 100 * (0.40*0.5 + 0.20*0.5 + 0.15*0.5 + 0.15*0.5 + 0.10*0.5) = 50
    assert compute_score(Factors(0.5, 0.5, 0.5, 0.5, 0.5)) == 50.0


def test_life_escalation_forces_critical_even_with_low_total():
    f = Factors(life=0.9)  # total = 36 -> would be MEDIUM
    score, tier = score_incident(f)
    assert score == 36.0
    assert tier == "CRITICAL"


def test_tier_bands():
    assert tier_for(80, 0.1) == "CRITICAL"
    assert tier_for(79.9, 0.1) == "HIGH"
    assert tier_for(60, 0.1) == "HIGH"
    assert tier_for(59.9, 0.1) == "MEDIUM"
    assert tier_for(30, 0.1) == "MEDIUM"
    assert tier_for(29.9, 0.1) == "LOW"


def test_people_factor_is_log_scaled():
    assert people_factor(0) == 0.0
    assert people_factor(50) == 1.0
    assert people_factor(1000) == 1.0
    # early people count for more than late ones
    assert people_factor(3) - people_factor(1) > people_factor(50) - people_factor(48)


def test_verification_needs_independent_reports():
    assert verification_factor(1) == 0.0
    assert verification_factor(2) < verification_factor(3) < verification_factor(4)
    assert verification_factor(10) == 1.0
