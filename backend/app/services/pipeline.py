"""Report processing pipeline: translate -> extract -> dedup/cluster -> score."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Incident, Report
from . import dedup, extraction, scoring
from .embeddings import get_embedder
from .translate import get_translator

LOW_CONFIDENCE_LIFE = 0.0  # reports with no recognised signal at all are flagged for call-back


def process_report(
    db: Session,
    text: str,
    channel: str = "text",
    language: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    english_text: str | None = None,
) -> tuple[Report, Incident]:
    """`english_text` lets a caller that already has an English version (voice, via Whisper's
    translate task) skip the text translator. `text` is always kept as the original."""
    if english_text is not None:
        english, lang = english_text, language or "en"
    else:
        english, lang = get_translator().to_english(text, language)
    ex = extraction.extract(english)
    embedding = get_embedder().embed(english)

    open_incidents = list(db.scalars(select(Incident).where(Incident.status != "resolved")))
    match = dedup.find_matching_incident(open_incidents, embedding, lat, lon)

    report = Report(
        channel=channel,
        original_text=text,
        language=lang,
        translated_text=english,
        lat=lat,
        lon=lon,
        needs_verification=(ex.life == 0.0 and ex.urgency == 0.0 and ex.isolation == 0.0),
    )

    if match is None:
        incident = Incident(
            incident_type=ex.incident_type,
            summary=english[:240],
            lat=lat,
            lon=lon,
            centroid=embedding,
            report_count=1,
            people_estimate=ex.people,
            f_life=0.0,
            f_urgency=0.0,
            f_isolation=0.0,
            status="open",
        )
        db.add(incident)
    else:
        incident = match
        incident.centroid = dedup.update_centroid(incident.centroid, incident.report_count, embedding)
        incident.report_count += 1
        incident.people_estimate = max(incident.people_estimate, ex.people)
        if incident.lat is None and lat is not None:
            incident.lat, incident.lon = lat, lon
        # a more severe type wins when reports are merged
        if ex.incident_type == "rescue":
            incident.incident_type = "rescue"

    # factors take the strongest evidence seen across all reports in the cluster
    incident.f_life = max(incident.f_life, ex.life)
    incident.f_urgency = max(incident.f_urgency, ex.urgency)
    incident.f_isolation = max(incident.f_isolation, ex.isolation)
    incident.f_people = scoring.people_factor(incident.people_estimate)
    incident.f_verification = scoring.verification_factor(incident.report_count)

    factors = scoring.Factors(
        life=incident.f_life,
        urgency=incident.f_urgency,
        people=incident.f_people,
        verification=incident.f_verification,
        isolation=incident.f_isolation,
    )
    incident.score, incident.tier = scoring.score_incident(factors)
    incident.updated_at = datetime.now(timezone.utc)

    report.incident = incident
    db.add(report)
    db.commit()
    db.refresh(incident)
    db.refresh(report)
    return report, incident
