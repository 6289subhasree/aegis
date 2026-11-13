"""Report processing pipeline: translate -> extract -> dedup/cluster -> score."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Incident, Report
from . import dedup, extraction, scoring
from .embeddings import get_embedder
from .packet_codec import PacketReport, decode_packet
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


def process_packet_report(db: Session, packet: PacketReport) -> tuple[Report, Incident]:
    """Process a verified 20-byte LoRa/SMS packet as a structured report."""
    summary_text = (
        f"[{packet.channel.upper()} Node {packet.node_id}] {packet.incident_type.title()}: "
        f"{packet.people} people affected. "
        f"Signals: L={int(packet.flag_life)}, U={int(packet.flag_urgency)}, A={int(packet.flag_isolation)}"
    )
    embedding = get_embedder().embed(f"{packet.incident_type} {summary_text}")
    open_incidents = list(db.scalars(select(Incident).where(Incident.status != "resolved")))
    match = dedup.find_matching_incident(open_incidents, embedding, packet.lat, packet.lon)

    report = Report(
        channel=packet.channel,
        original_text=summary_text,
        language=packet.language,
        translated_text=summary_text,
        lat=packet.lat,
        lon=packet.lon,
        needs_verification=not packet.flag_life,
    )

    life_val = 1.0 if packet.flag_life else 0.0
    urgency_val = 0.95 if packet.flag_urgency else 0.2
    isolation_val = 1.0 if packet.flag_isolation else 0.1

    if match is None:
        incident = Incident(
            incident_type=packet.incident_type,
            summary=summary_text[:240],
            lat=packet.lat,
            lon=packet.lon,
            centroid=embedding,
            report_count=1,
            people_estimate=packet.people,
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
        incident.people_estimate = max(incident.people_estimate, packet.people)
        if incident.lat is None and packet.lat is not None:
            incident.lat, incident.lon = packet.lat, packet.lon
        if packet.incident_type == "rescue":
            incident.incident_type = "rescue"

    incident.f_life = max(incident.f_life, life_val)
    incident.f_urgency = max(incident.f_urgency, urgency_val)
    incident.f_isolation = max(incident.f_isolation, isolation_val)
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

