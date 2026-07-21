"""
Bias-aware assignment: distribute transcripts to auditors so no auditor gets
too many from the same "agent" bucket (spread) and workload is balanced.
"""
from datetime import date
from ..data.models import Assignment, Auditor


def _agent_bucket(transcript_id: str, num_buckets: int = 10) -> int:
    """Derived bucket for spread (simulates agent/source diversity)."""
    return hash(transcript_id) % num_buckets


def distribute(
    transcript_ids: list[str],
    auditors: list[Auditor],
    assigned_date: str,
) -> list[Assignment]:
    """
    Assign each transcript to an auditor. Spread by bucket (bias-aware) and balance count.
    Returns list of Assignment (no id, status=pending).
    """
    if not transcript_ids or not auditors:
        return []
    auditor_ids = [a.id for a in auditors]
    # Sort by bucket so round-robin gives each auditor a mix (bias-aware spread)
    sorted_ids = sorted(transcript_ids, key=lambda tid: _agent_bucket(tid))
    assignments = []
    for i, tid in enumerate(sorted_ids):
        auditor_id = auditor_ids[i % len(auditor_ids)]
        assignments.append(Assignment(
            id=None,
            transcript_id=tid,
            auditor_id=auditor_id,
            assigned_date=assigned_date,
            assigned_at=None,
            completed_at=None,
            status="pending",
        ))
    return assignments


def run_daily_assignment(
    store,
    transcript_ids: list[str],
    assigned_date: str | None = None,
) -> int:
    """
    Create assignments for transcript_ids that are not already assigned on assigned_date.
    Uses store.list_auditors(), store.get_transcript_ids_assigned_on_date(), store.insert_assignments().
    Returns number of new assignments created.
    """
    assigned_date = assigned_date or date.today().isoformat()
    already = store.get_transcript_ids_assigned_on_date(assigned_date)
    to_assign = [tid for tid in transcript_ids if tid not in already]
    auditors = store.list_auditors()
    if not auditors:
        return 0
    new = distribute(to_assign, auditors, assigned_date)
    if new:
        store.insert_assignments(new)
    return len(new)
