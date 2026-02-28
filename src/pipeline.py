"""
Pipeline: generate transcripts, run audit, score, and persist.
Call this to populate the DB before viewing the dashboard.
"""
import time
from typing import Optional

from .data.store import get_store
from .data.models import AuditRun
from .synthetic.generator import generate_transcripts
from .audit.engine import audit_transcript
from .audit.llm_audit import get_llm_outcome_summary
from .scoring.scorer import score_findings

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
        findings = audit_transcript(t)
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
