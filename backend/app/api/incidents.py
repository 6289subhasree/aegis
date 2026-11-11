from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Incident, OverrideLog
from ..schemas import IncidentDetail, IncidentOut, OverrideIn, StatusIn
from .serializers import TIER_RANK, effective_tier, incident_detail, incident_out

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _get(db: Session, incident_id: int) -> Incident:
    inc = db.get(Incident, incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.get("", response_model=list[IncidentOut])
def ranked_queue(
    include_resolved: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """The prioritised queue: severity first, then score, then most recent. Not arrival order."""
    stmt = select(Incident)
    if not include_resolved:
        stmt = stmt.where(Incident.status != "resolved")
    incidents = list(db.scalars(stmt))
    incidents.sort(
        key=lambda i: (TIER_RANK[effective_tier(i)], i.score, i.updated_at.timestamp()),
        reverse=True,
    )
    return [incident_out(i) for i in incidents[:limit]]


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    return incident_detail(_get(db, incident_id))


@router.post("/{incident_id}/override", response_model=IncidentOut)
def override_tier(incident_id: int, body: OverrideIn, db: Session = Depends(get_db)):
    """Human in the loop: an authorised responder re-ranks an incident. Logged for recalibration."""
    inc = _get(db, incident_id)
    db.add(
        OverrideLog(
            incident_id=inc.id,
            from_tier=effective_tier(inc),
            to_tier=body.tier,
            note=body.note,
        )
    )
    inc.override_tier = body.tier
    inc.override_note = body.note or None
    db.commit()
    db.refresh(inc)
    return incident_out(inc)


@router.delete("/{incident_id}/override", response_model=IncidentOut)
def clear_override(incident_id: int, db: Session = Depends(get_db)):
    inc = _get(db, incident_id)
    inc.override_tier = None
    inc.override_note = None
    db.commit()
    db.refresh(inc)
    return incident_out(inc)


@router.post("/{incident_id}/status", response_model=IncidentOut)
def set_status(incident_id: int, body: StatusIn, db: Session = Depends(get_db)):
    inc = _get(db, incident_id)
    inc.status = body.status
    db.commit()
    db.refresh(inc)
    return incident_out(inc)
