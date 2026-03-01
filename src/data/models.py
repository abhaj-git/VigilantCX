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
    outcome_summary: Optional[str] = None  # LLM-generated concise reason for outcome


# DPA (Desktop Process Analytics): screen events and computed process metrics
# Idle time = time with no screen activity (gaps between events). High = disengaged/distracted.
# Dwell time = time on a single screen before switching. High = slow/stuck on one screen.
@dataclass
class DPAEvent:
    transcript_id: str
    timestamp_sec: float
    screen_id: str  # e.g. login, account_summary, payment, disclosure, wrap_up


@dataclass
class DPAMetrics:
    transcript_id: str
    call_duration_sec: float
    idle_sec: float  # total time with no screen activity (gaps between events)
    idle_ratio: float  # idle_sec / call_duration_sec (0–1)
    max_dwell_sec: float  # longest time on any single screen
    dwell_by_screen: dict  # screen_id -> seconds on that screen
