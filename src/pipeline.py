"""
Pipeline: generate transcripts, run audit, score, and persist.
Call this to populate the DB before viewing the dashboard.
"""
import time
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from .data.store import get_store
from .data.models import AuditRun
from .synthetic.generator import generate_transcripts
from .audit.engine import audit_transcript
from .audit.llm_audit import get_llm_outcome_summary
from .scoring.scorer import score_findings
from .dpa.generator import generate_dpa_for_transcript

# Delay between LLM calls to avoid OpenAI rate limit
LLM_CALL_DELAY_SECONDS = 1.5


def run_pipeline(store=None, max_per_scenario: int = 1, use_llm: bool = False) -> list[str]:
    """
    Generate transcripts, audit each, score, optionally get LLM outcome summary, and save.
    Returns list of transcript IDs. Set use_llm=False to skip LLM (no OPENAI_API_KEY needed).
    """
    store = store or get_store()
    generated = generate_transcripts(store=store, max_per_scenario=max_per_scenario)
    ids = []
    for t in generated:
        dpa_metrics = generate_dpa_for_transcript(t, store)
        findings = audit_transcript(t, dpa_metrics=dpa_metrics)
        store.insert_findings(t.id, findings)
        score, severity_band, has_critical = score_findings(findings)
        outcome_summary = None
        if use_llm:
            try:
                outcome_summary = get_llm_outcome_summary(t, findings, severity_band)
            except Exception:
                outcome_summary = None  # don't fail whole pipeline on one LLM error
            time.sleep(LLM_CALL_DELAY_SECONDS)  # avoid rate limit
        store.insert_audit_run(AuditRun(
            id=None,
            transcript_id=t.id,
            score=score,
            severity_band=severity_band,
            has_critical=has_critical,
            outcome_summary=outcome_summary,
        ))
        ids.append(t.id)
    return ids


def backfill_llm_summaries(
    store=None,
    api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> tuple[int, Optional[str]]:
    """
    For all existing transcripts, call the LLM (Gemini or OpenAI) and update outcome summary.
    Returns (number_updated, error_message). Set GEMINI_API_KEY or OPENAI_API_KEY in env/Secrets.
    """
    store = store or get_store()
    from .audit.llm_audit import get_llm_outcome_summary
    ids = store.list_transcript_ids()
    updated = 0
    first_error = None
    for tid in ids:
        t = store.get_transcript(tid)
        if not t:
            continue
        run = store.get_latest_audit_run(tid)
        if not run:
            continue
        findings = store.get_findings(tid)
        try:
            summary = get_llm_outcome_summary(
                t, findings, run.severity_band,
                api_key=api_key, gemini_api_key=gemini_api_key,
            )
        except Exception as e:
            if first_error is None:
                first_error = str(e)
            continue
        if summary:
            store.update_audit_run_outcome_summary(tid, summary)
            updated += 1
        time.sleep(LLM_CALL_DELAY_SECONDS)  # avoid rate limit
    return updated, first_error


def backfill_dpa(store=None) -> int:
    """
    Generate synthetic DPA for all transcripts that don't have it; re-run audit (with process rules)
    and update score. If metrics exist but are invalid (idle_ratio out of 0–1), recompute from events.
    Returns number of transcripts updated.
    """
    from .dpa.generator import compute_metrics_from_events
    store = store or get_store()
    ids = store.list_transcript_ids()
    updated = 0
    for tid in ids:
        t = store.get_transcript(tid)
        if not t:
            continue
        dpa_metrics = store.get_dpa_metrics(tid)
        if dpa_metrics and 0 <= dpa_metrics.idle_ratio <= 1:
            continue
        if dpa_metrics and (dpa_metrics.idle_ratio < 0 or dpa_metrics.idle_ratio > 1):
            events = store.get_dpa_events(tid)
            if events:
                m = compute_metrics_from_events(tid, events, dpa_metrics.call_duration_sec)
                store.insert_dpa_metrics(m)
                dpa_metrics = m
        else:
            generate_dpa_for_transcript(t, store)
            dpa_metrics = store.get_dpa_metrics(tid)
        if not dpa_metrics:
            continue
        store.delete_findings(tid)
        findings = audit_transcript(t, dpa_metrics=dpa_metrics)
        store.insert_findings(tid, findings)
        score, severity_band, has_critical = score_findings(findings)
        run = store.get_latest_audit_run(tid)
        if run:
            store.update_latest_audit_run(tid, score, severity_band, has_critical)
        updated += 1
    return updated
