"""
Compliance overrides: mark transcript or finding as compliant; used before filtering.
"""
from datetime import datetime
from ..data.models import Override
from ..data.store import Store


def add_override(
    store: Store,
    transcript_id: str,
    overridden_by: str,
    reason: str,
    finding_id: int | None = None,
    expires_at: str | None = None,
) -> None:
    """Record an override for a transcript (or a specific finding)."""
    o = Override(
        transcript_id=transcript_id,
        overridden_by=overridden_by,
        reason=reason,
        finding_id=finding_id,
        expires_at=expires_at,
    )
    store.add_override(o)


def is_transcript_overridden(store: Store, transcript_id: str) -> bool:
    """True if transcript has a transcript-level override that is not expired."""
    overrides = store.get_overrides_for_transcript(transcript_id)
    now = datetime.utcnow().isoformat() + "Z"
    for o in overrides:
        if o.finding_id is None and (o.expires_at is None or o.expires_at > now):
            return True
    return False


def apply_overrides(
    transcript_ids: list[str],
    store: Store,
    exclude_overridden: bool = True,
) -> list[str]:
    """
    Return transcript IDs after excluding those with an active transcript-level override.
    """
    if not exclude_overridden:
        return transcript_ids
    return [tid for tid in transcript_ids if not is_transcript_overridden(store, tid)]
