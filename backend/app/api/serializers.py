from ..models import Incident
from ..schemas import FactorBreakdown, IncidentDetail, IncidentOut, ReportOut
from ..services.scoring import Factors, escalation_reason

TIER_RANK = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


def effective_tier(inc: Incident) -> str:
    return inc.override_tier or inc.tier


def _base(inc: Incident) -> dict:
    return dict(
        id=inc.id,
        incident_type=inc.incident_type,
        summary=inc.summary,
        lat=inc.lat,
        lon=inc.lon,
        report_count=inc.report_count,
        people_estimate=inc.people_estimate,
        score=inc.score,
        tier=inc.tier,
        escalation=escalation_reason(
            Factors(inc.f_life, inc.f_urgency, inc.f_people, inc.f_verification, inc.f_isolation),
            inc.score,
            inc.tier,
        ),
        effective_tier=effective_tier(inc),
        override_tier=inc.override_tier,
        override_note=inc.override_note,
        status=inc.status,
        factors=FactorBreakdown(
            life=inc.f_life,
            urgency=inc.f_urgency,
            people=inc.f_people,
            verification=inc.f_verification,
            isolation=inc.f_isolation,
        ),
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


def incident_out(inc: Incident) -> IncidentOut:
    return IncidentOut(**_base(inc))


def incident_detail(inc: Incident) -> IncidentDetail:
    return IncidentDetail(**_base(inc), reports=[ReportOut.model_validate(r) for r in inc.reports])
