from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Tier = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


class ReportIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    channel: Literal["text", "sms", "voice", "lora"] = "text"
    language: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)


class PacketIn(BaseModel):
    packet_base64: str = Field(min_length=28, max_length=28, description="28-char Base64 SMS or LoRa frame")



class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int | None
    channel: str
    original_text: str
    language: str
    translated_text: str
    lat: float | None
    lon: float | None
    needs_verification: bool
    received_at: datetime


class FactorBreakdown(BaseModel):
    life: float
    urgency: float
    people: float
    verification: float
    isolation: float


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_type: str
    summary: str
    lat: float | None
    lon: float | None
    report_count: int
    people_estimate: int
    score: float
    tier: Tier
    escalation: str | None = None
    effective_tier: Tier
    override_tier: Tier | None
    override_note: str | None
    status: str
    factors: FactorBreakdown
    created_at: datetime
    updated_at: datetime


class IncidentDetail(IncidentOut):
    reports: list[ReportOut]


class OverrideIn(BaseModel):
    tier: Tier
    note: str = Field(default="", max_length=500)


class StatusIn(BaseModel):
    status: Literal["open", "dispatched", "resolved"]


class IngestResult(BaseModel):
    report: ReportOut
    incident: IncidentOut
    merged: bool


class VoiceIngestResult(IngestResult):
    transcript: str  # in the spoken language
    english: str
    language: str
