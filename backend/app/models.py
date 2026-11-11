from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    """A cluster of one or more reports describing the same real-world emergency."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_type: Mapped[str] = mapped_column(String(32), default="other")
    summary: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid: Mapped[list | None] = mapped_column(JSON, nullable=True)  # mean embedding
    report_count: Mapped[int] = mapped_column(Integer, default=1)

    # Severity factors, each in [0, 1]
    f_life: Mapped[float] = mapped_column(Float, default=0.0)
    f_urgency: Mapped[float] = mapped_column(Float, default=0.0)
    f_people: Mapped[float] = mapped_column(Float, default=0.0)
    f_verification: Mapped[float] = mapped_column(Float, default=0.0)
    f_isolation: Mapped[float] = mapped_column(Float, default=0.0)
    people_estimate: Mapped[int] = mapped_column(Integer, default=0)

    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    tier: Mapped[str] = mapped_column(String(16), default="LOW", index=True)

    # Responder override (human in the loop)
    override_tier: Mapped[str | None] = mapped_column(String(16), nullable=True)
    override_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | dispatched | resolved

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    reports: Mapped[list["Report"]] = relationship(back_populates="incident")


class Report(Base):
    """A single raw message from a citizen."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(16), default="text")  # text | sms | voice | lora
    original_text: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    translated_text: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_verification: Mapped[bool] = mapped_column(default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incident: Mapped[Incident | None] = relationship(back_populates="reports")


class OverrideLog(Base):
    """Every responder override is logged; later used to recalibrate the score weights."""

    __tablename__ = "override_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    from_tier: Mapped[str] = mapped_column(String(16))
    to_tier: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
