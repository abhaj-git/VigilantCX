"""
Filter: keep only transcripts that are below threshold OR have critical finding.
Used for dashboard (actionable items only).
"""
from ..config_loader import get_score_threshold
from ..data.models import Transcript
from ..data.store import Store


def filter_actionable(
    transcript_ids: list[str],
    store: Store,
    score_threshold: float | None = None,
    exclude_overridden: bool = True,
) -> list[str]:
    """
    Return transcript IDs that should be shown on dashboard:
    score >= threshold (failing quality bar) OR has_critical, optionally excluding overridden.
    """
    threshold = score_threshold if score_threshold is not None else get_score_threshold()
    overridden = store.get_all_overridden_transcript_ids() if exclude_overridden else set()
    actionable = []
    for tid in transcript_ids:
        if tid in overridden:
            continue
        run = store.get_latest_audit_run(tid)
        if not run:
            continue
        if run.has_critical or run.score >= threshold:
            actionable.append(tid)
    return actionable
