from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import IngestResult, ReportIn, ReportOut
from ..services.pipeline import process_report
from ..services.stt import get_stt
from .serializers import incident_out

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=IngestResult, status_code=201)
def submit_report(payload: ReportIn, db: Session = Depends(get_db)):
    """Submit a text/SMS/LoRa report. It is translated, clustered, scored and ranked."""
    from ..models import Incident
    from sqlalchemy import func, select

    before = db.scalar(select(func.count()).select_from(Incident))
    report, incident = process_report(
        db, payload.text, payload.channel, payload.language, payload.lat, payload.lon
    )
    after = db.scalar(select(func.count()).select_from(Incident))
    return IngestResult(
        report=ReportOut.model_validate(report),
        incident=incident_out(incident),
        merged=after == before,
    )


@router.post("/voice", response_model=IngestResult, status_code=201)
async def submit_voice_report(
    audio: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """Submit a voice report. Needs STT_BACKEND=whisper."""
    from ..models import Incident
    from sqlalchemy import func, select

    try:
        text, lang = get_stt().transcribe(await audio.read())
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    if not text.strip():
        raise HTTPException(status_code=422, detail="No speech detected in audio")

    before = db.scalar(select(func.count()).select_from(Incident))
    report, incident = process_report(db, text, "voice", lang, lat, lon)
    after = db.scalar(select(func.count()).select_from(Incident))
    return IngestResult(
        report=ReportOut.model_validate(report),
        incident=incident_out(incident),
        merged=after == before,
    )
