from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Incident
from ..schemas import IngestResult, PacketIn, ReportIn, ReportOut, VoiceIngestResult
from ..services.packet_codec import packet_from_base64_sms
from ..services.pipeline import process_packet_report, process_report
from ..services.stt import get_stt
from .serializers import incident_out

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_AUDIO_BYTES = 10 * 1024 * 1024


def _incident_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Incident)) or 0


@router.post("", response_model=IngestResult, status_code=201)
def submit_report(payload: ReportIn, db: Session = Depends(get_db)):
    """Submit a text/SMS/LoRa report. It is translated, clustered, scored and ranked."""
    before = _incident_count(db)
    report, incident = process_report(
        db, payload.text, payload.channel, payload.language, payload.lat, payload.lon
    )
    return IngestResult(
        report=ReportOut.model_validate(report),
        incident=incident_out(incident),
        merged=_incident_count(db) == before,
    )


@router.post("/packet", response_model=IngestResult, status_code=201)
def submit_packet(payload: PacketIn, db: Session = Depends(get_db)):
    """Ingest a 28-character Base64 encoded 20-byte LoRa/SMS packet.

    Gateway verifies CRC-16, parses flags and geolocation, and feeds pipeline.
    """
    try:
        packet = packet_from_base64_sms(payload.packet_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    before = _incident_count(db)
    report, incident = process_packet_report(db, packet)
    return IngestResult(
        report=ReportOut.model_validate(report),
        incident=incident_out(incident),
        merged=_incident_count(db) == before,
    )



@router.post("/voice", response_model=VoiceIngestResult, status_code=201)
async def submit_voice_report(
    audio: UploadFile = File(...),
    lat: float | None = Form(default=None, ge=-90, le=90),
    lon: float | None = Form(default=None, ge=-180, le=180),
    language: str | None = Form(default=None, max_length=8),
    db: Session = Depends(get_db),
):
    """Submit a voice report. Speech is transcribed locally by Whisper (STT_BACKEND=whisper),
    translated to English if needed, then processed like any other report.

    `language` is an optional hint (e.g. "hi"); leave it empty to auto-detect.
    """
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=422, detail="Empty audio upload")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio too large (max 10 MB)")

    try:
        transcript = get_stt().transcribe(data, language or None)
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    if not transcript.english.strip():
        raise HTTPException(status_code=422, detail="No speech detected in the recording")

    before = _incident_count(db)
    report, incident = process_report(
        db,
        transcript.text,
        "voice",
        transcript.language,
        lat,
        lon,
        english_text=transcript.english,
    )
    return VoiceIngestResult(
        report=ReportOut.model_validate(report),
        incident=incident_out(incident),
        merged=_incident_count(db) == before,
        transcript=transcript.text,
        english=transcript.english,
        language=transcript.language,
    )
