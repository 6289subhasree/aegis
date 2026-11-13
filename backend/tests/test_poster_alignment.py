"""Direct verification of Poster specifications and worked examples.

Covers:
- Section 06: 6-packet bad order demo (5th and 6th life-threat packets rank #1 and #2)
- Section 09: Bengali worked example S = 91 (CRITICAL)
- Section 08: Escalation rules
"""

from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.demo import PACKET_SCENARIO, load_packet_scenario, reset_all
from app.models import Incident
from app.services import extraction, scoring
from app.services.pipeline import process_packet_report, process_report


def test_section_06_packet_demo_leapfrog():
    """Verify Poster Section 06 claim:
    'Demo (tested): 6 packets arrive in bad order; the two life-threat packets
    (5th and 6th to arrive) are ranked #1 and #2.'
    """
    engine = db_module.make_engine("sqlite:///:memory:")
    db_module.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = Session()

    res = load_packet_scenario(db)
    assert res["packets"] == 6

    # Fetch ranked queue (sorted descending by score)
    incidents = (
        db.query(Incident)
        .filter(Incident.status != "resolved")
        .order_by(Incident.score.desc())
        .all()
    )

    # 6 packets collapse into 4 distinct incidents due to deduplication of farmland & rooftop
    assert len(incidents) == 4

    # The top incident (#1) MUST be the rooftop rescue (packets 5 and 6)
    rank1 = incidents[0]
    assert rank1.incident_type == "rescue"
    assert rank1.tier == "CRITICAL"
    assert rank1.f_life == 1.0
    assert rank1.report_count == 2  # Packets 5 and 6 merged into 1 incident cluster
    assert rank1.score >= 80.0

    # The second incident (#2) is the isolated cut-off community / bridge collapse
    rank2 = incidents[1]
    assert rank2.incident_type == "collapse"
    assert rank2.tier == "HIGH"
    assert rank2.f_isolation >= 0.8
    assert rank2.f_urgency >= 0.7

    # Lower priority incidents are routine floods and muddy roads
    assert incidents[2].score < rank2.score
    assert incidents[3].score < incidents[2].score
    db.close()


def test_section_09_worked_example_bengali_scoring():
    """Verify Poster Section 09 Worked Example:
    Input: "ছাদে ৫ জন আটকে, জল বাড়ছে"
    Translation: "5 people stuck on roof, water rising"
    Factors: L=1.00, U=0.95, P=0.46, V=1.00, A=1.00
    Score: S = 40 + 19 + 6.9 + 15 + 10 = 90.9 -> S = 91 -> CRITICAL
    """
    # 1. Extraction from English translated text
    text_en = "5 people stuck on roof, water rising"
    ex = extraction.extract(text_en)

    assert ex.incident_type == "rescue"
    assert ex.people == 5
    assert ex.life == 1.0  # "stuck" / "roof" trigger 1.0

    # 2. Factor calculations
    p_factor = round(scoring.people_factor(5), 2)
    assert p_factor == 0.46  # ln(1+5)/ln(1+50) = 0.4557 -> 0.46

    # V with 4 corroborating reports in cluster:
    v_factor = scoring.verification_factor(4)
    assert v_factor == 1.0

    # Worked example factors:
    f = scoring.Factors(
        life=1.00,
        urgency=0.95,
        people=0.46,
        verification=1.00,
        isolation=1.00,
    )

    # 3. Exact formula verification
    score = scoring.compute_score(f)
    # 40 + 19 + 6.9 + 15 + 10 = 90.9 -> round to 91.0
    assert round(score) == 91

    tier = scoring.tier_for(score, life=f.life, urgency=f.urgency, isolation=f.isolation)
    assert tier == "CRITICAL"


def test_escalation_rules_match_poster_section_08():
    """Verify Poster Section 08:
    Rule 1: L > 0.8 => CRITICAL.
    Rule 2: isolated (A >= 0.8) and urgent (U >= 0.7) or life risk (L >= 0.5) => at least HIGH.
    """
    # Rule 1
    tier1 = scoring.tier_for(score=35.0, life=0.9, urgency=0.0, isolation=0.0)
    assert tier1 == "CRITICAL"

    # Rule 2: isolated + urgent
    tier2 = scoring.tier_for(score=25.0, life=0.0, urgency=0.75, isolation=0.85)
    assert tier2 == "HIGH"

    # Rule 2: isolated + life risk
    tier3 = scoring.tier_for(score=25.0, life=0.55, urgency=0.0, isolation=0.85)
    assert tier3 == "HIGH"


def test_section_02_illustrative_scores_and_p_formula_alignment():
    """Verify Poster Section 02 illustrative scores and formula parameters:
    1. Scores: 91 (CRITICAL), 72 (HIGH), 38 (MEDIUM), 15 (LOW)
    2. People saturation: ln(1+n)/ln(51) yields 0.46 for n=5 (ln(150) would yield 0.36)
    3. Rule 1: L > 0.8 correctly prevents single 0.8 life phrases from premature CRITICAL
    """
    # 1. Tier boundaries for illustrative scores
    assert scoring.band_tier(91.0) == "CRITICAL"
    assert scoring.band_tier(72.0) == "HIGH"
    assert scoring.band_tier(38.0) == "MEDIUM"
    assert scoring.band_tier(15.0) == "LOW"

    # 2. People factor saturation
    # With n=5 people: ln(6)/ln(51) = 1.79176 / 3.93183 = 0.4557 -> rounds to 0.46
    import math
    p5_code = scoring.people_factor(5)
    assert round(p5_code, 2) == 0.46
    p5_hypothetical_150 = math.log1p(5) / math.log1p(150)
    assert round(p5_hypothetical_150, 2) == 0.36  # proves ln(51) is required for poster's 0.46!

    # 3. Rule 1 boundary: exactly 0.8 should NOT trigger CRITICAL by rule alone
    tier_at_08 = scoring.tier_for(score=25.0, life=0.8, urgency=0.0, isolation=0.0)
    assert tier_at_08 == "LOW"
    tier_above_08 = scoring.tier_for(score=25.0, life=0.81, urgency=0.0, isolation=0.0)
    assert tier_above_08 == "CRITICAL"


def test_load_poster_tier_scenario_reproduces_exact_benchmark():
    """Verify demo.load_poster_tier_scenario creates the exact 4-tier benchmark."""
    from app.demo import load_poster_tier_scenario
    engine = db_module.make_engine("sqlite:///:memory:")
    db_module.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = Session()

    out = load_poster_tier_scenario(db)
    assert out["incidents"] == 4
    assert out["scores"] == [91.0, 72.0, 38.0, 15.0]

    incidents = db.query(Incident).order_by(Incident.score.desc()).all()
    assert [inc.score for inc in incidents] == [91.0, 72.0, 38.0, 15.0]
    assert [inc.tier for inc in incidents] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    db.close()
