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


def test_isolation_with_urgency_escalates_to_high():
    # bridge collapsed, village cut off: U=0.7, A=1.0, no life signal -> band says LOW
    f = Factors(urgency=0.7, isolation=1.0, verification=0.33)
    score, tier = score_incident(f)
    assert score < 30
    assert tier == "HIGH"


def test_isolation_with_life_risk_escalates_to_high():
    f = Factors(life=0.6, isolation=1.0)  # e.g. pregnant woman, road cut off
    assert score_incident(f)[1] == "HIGH"


def test_isolation_alone_does_not_escalate():
    f = Factors(isolation=1.0)  # road blocked, nothing urgent
    assert score_incident(f)[1] == "LOW"


def test_escalation_never_lowers_a_tier():
    f = Factors(life=0.6, urgency=0.9, people=1.0, verification=1.0, isolation=1.0)
    score, tier = score_incident(f)
    assert tier == "CRITICAL" and score >= 80


def test_escalation_reason_is_reported():
    from app.services.scoring import escalation_reason

    f = Factors(urgency=0.7, isolation=1.0)
    score, tier = score_incident(f)
    assert "isolated community" in escalation_reason(f, score, tier)
    f2 = Factors(life=0.9)
    s2, t2 = score_incident(f2)
    assert "threat to life" in escalation_reason(f2, s2, t2)
    f3 = Factors(life=0.5, urgency=0.5)
    s3, t3 = score_incident(f3)
    assert escalation_reason(f3, s3, t3) is None
