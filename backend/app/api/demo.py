from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import demo
from ..config import get_settings
from ..db import get_db

router = APIRouter(prefix="/demo", tags=["demo"])


def _require_demo_mode() -> None:
    if not get_settings().demo_mode:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")


@router.post("/load", dependencies=[Depends(_require_demo_mode)])
def load_demo_scenario(db: Session = Depends(get_db)):
    """Submit the illustrative flood scenario (10 reports, arrival order deliberately bad)."""
    return demo.load_scenario(db)


@router.post("/reset", dependencies=[Depends(_require_demo_mode)])
def reset_demo(db: Session = Depends(get_db)):
    """Delete all reports, incidents and override logs."""
    demo.reset_all(db)
    return {"status": "cleared"}
