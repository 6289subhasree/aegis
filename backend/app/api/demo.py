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


@router.post("/load-packets", dependencies=[Depends(_require_demo_mode)])
def load_packet_scenario(db: Session = Depends(get_db)):
    """Submit the 6-packet LoRa/SMS demo from Poster Section 06.
    6 packets arrive out of order; the 5th and 6th (life threat) rank #1 and #2.
    """
    return demo.load_packet_scenario(db)


@router.post("/load-poster-tiers", dependencies=[Depends(_require_demo_mode)])
def load_poster_tier_scenario(db: Session = Depends(get_db)):
    """Load the exact 4-tier calibration benchmark from Poster Section 02 (Scores: 91, 72, 38, 15)."""
    return demo.load_poster_tier_scenario(db)



@router.post("/reset", dependencies=[Depends(_require_demo_mode)])
def reset_demo(db: Session = Depends(get_db)):
    """Delete all reports, incidents and override logs."""
    demo.reset_all(db)
    return {"status": "cleared"}
