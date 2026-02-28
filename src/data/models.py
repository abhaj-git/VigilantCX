"""Data models for transcripts, findings, overrides."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TranscriptTurn:
    speaker: str  # "agent" | "customer" | "dealer"
    text: str
    segment: Optional[str] = None  # "greeting" | "body" | "closing"


@dataclass
class Transcript:
    id: str
    persona_id: str  # "collections" | "ram"
    language: str  # "en" | "es"
    intended_risk_level: str  # "good" | "moderate" | "high" | "critical"
    scenario_id: str
    expected_findings: list[str]  # rule ids
    turns: list[TranscriptTurn]
    created_at: Optional[str] = None
    # Populated after audit
    score: Optional[float] = None
    severity_band: Optional[str] = None
    has_critical: Optional[bool] = None


@dataclass
class Finding:
    id: Optional[int]
    transcript_id: str
    rule_id: str
    passed: bool
    severity: str  # "critical" | "high" | "moderate" | "low"
    reason: str  # human-readable
    snippet: Optional[str] = None
    weight: Optional[float] = None


@dataclass
class Override:
    transcript_id: str
    overridden_by: str
    reason: str
    id: Optional[int] = None
    finding_id: Optional[int] = None  # null = transcript-level override
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class AuditRun:
    id: Optional[int]
    transcript_id: str
    score: float
    severity_band: str
    has_critical: bool
    run_at: Optional[str] = None
