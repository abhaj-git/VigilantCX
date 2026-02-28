"""
Pipeline: generate transcripts, run audit, score, and persist.
Call this to populate the DB before viewing the dashboard.
"""
from .data.store import get_store
from .data.models import AuditRun
from .synthetic.generator import generate_transcripts
from .audit.engine import audit_transcript
from .scoring.scorer import score_findings


def run_pipeline(store=None, max_per_scenario: int = 1) -> list[str]:
    """
    Generate transcripts, audit each, score, and save findings + audit_run.
    Returns list of transcript IDs.
    """
    store = store or get_store()
    generated = generate_transcripts(store=store, max_per_scenario=max_per_scenario)
    ids = []
    for t in generated:
        findings = audit_transcript(t)
        store.insert_findings(t.id, findings)
        score, severity_band, has_critical = score_findings(findings)
        store.insert_audit_run(AuditRun(
            id=None,
            transcript_id=t.id,
            score=score,
            severity_band=severity_band,
            has_critical=has_critical,
        ))
        ids.append(t.id)
    return ids
