"""
Synthetic DPA events and computed idle/dwell metrics.
- Idle time = time with no screen activity (before first event, after last event, or gaps). High = disengaged.
- Dwell time = time on a single screen before switching. High = slow or stuck on one screen.
"""
import random
from typing import Optional

from ..data.models import DPAMetrics, Transcript

# Screens by persona (order can vary in synthetic data)
COLLECTIONS_SCREENS = ["login", "account_summary", "payment", "disclosure", "notes", "wrap_up"]
RAM_SCREENS = ["login", "dealer_lookup", "documentation", "disclosure", "notes", "wrap_up"]

# Thresholds (sec): gaps above this count as "idle" when computing; also used for "bad" synthetic
IDLE_GAP_THRESHOLD_SEC = 30
# Call duration: infer from transcript length if not provided
DEFAULT_CALL_DURATION_SEC = 240
SEC_PER_TURN = 25


def _call_duration_sec(transcript: Transcript) -> float:
    """Infer call duration from number of turns."""
    n = len(transcript.turns) if transcript.turns else 10
    return max(60, min(600, n * SEC_PER_TURN))


def generate_synthetic_events(
    transcript_id: str,
    persona_id: str,
    call_duration_sec: float,
    *,
    high_idle: bool = False,
    high_dwell: bool = False,
    seed: Optional[int] = None,
) -> list[tuple[float, str]]:
    """Generate synthetic DPA events (timestamp_sec, screen_id). Optionally bias for high idle or high dwell."""
    rng = random.Random(seed if seed is not None else hash(transcript_id) % (2**32))
    screens = COLLECTIONS_SCREENS if persona_id == "collections" else RAM_SCREENS
    events = []
    t = 0.0
    if high_idle:
        # Long idle at start, then a few events with big gaps
        t = rng.uniform(60, 120)
        events.append((t, screens[0]))
        for i in range(1, min(4, len(screens))):
            t += rng.uniform(90, 180)
            events.append((t, screens[i]))
    elif high_dwell:
        # Normal start but one screen held very long
        t = rng.uniform(5, 20)
        events.append((t, screens[0]))
        dwell_screen = rng.choice(screens[1:-1])
        t += rng.uniform(300, 420)
        events.append((t, dwell_screen))
        for s in screens:
            if s == dwell_screen:
                continue
            t += rng.uniform(15, 60)
            if t < call_duration_sec - 10:
                events.append((t, s))
    else:
        # Normal: spread events across call
        for i, screen in enumerate(screens):
            t += rng.uniform(15, 60)
            if t >= call_duration_sec - 5:
                break
            events.append((t, screen))
    return events


def compute_metrics_from_events(
    transcript_id: str,
    events: list[tuple[float, str]],
    call_duration_sec: float,
) -> DPAMetrics:
    """
    Compute idle and dwell from event list.
    Idle = time with no screen activity (before first event + after last event).
    Dwell = time on each screen (from one event to the next transition).
    """
    if not events:
        return DPAMetrics(
            transcript_id=transcript_id,
            call_duration_sec=call_duration_sec,
            idle_sec=call_duration_sec,
            idle_ratio=1.0,
            max_dwell_sec=0.0,
            dwell_by_screen={},
        )
    sorted_events = sorted(events, key=lambda x: x[0])
    first_ts = max(0, sorted_events[0][0])
    last_ts = min(sorted_events[-1][0], call_duration_sec)
    idle_sec = max(0, first_ts + (call_duration_sec - last_ts))
    dwell_by_screen = {}
    for i in range(len(sorted_events) - 1):
        t_cur, screen = sorted_events[i]
        t_next = sorted_events[i + 1][0]
        seg = min(t_next - t_cur, call_duration_sec - t_cur)
        if seg > 0:
            dwell_by_screen[screen] = dwell_by_screen.get(screen, 0) + seg
    # Last event's dwell: from last_ts to end of call
    if sorted_events and call_duration_sec > last_ts:
        _, last_screen = sorted_events[-1]
        seg = call_duration_sec - last_ts
        dwell_by_screen[last_screen] = dwell_by_screen.get(last_screen, 0) + seg
    max_dwell_sec = max(dwell_by_screen.values()) if dwell_by_screen else 0.0
    idle_ratio = (idle_sec / call_duration_sec) if call_duration_sec else 0.0
    idle_ratio = max(0, min(1, idle_ratio))
    return DPAMetrics(
        transcript_id=transcript_id,
        call_duration_sec=call_duration_sec,
        idle_sec=round(idle_sec, 1),
        idle_ratio=round(idle_ratio, 3),
        max_dwell_sec=round(max_dwell_sec, 1),
        dwell_by_screen={k: round(v, 1) for k, v in dwell_by_screen.items()},
    )


def generate_dpa_for_transcript(
    transcript: Transcript,
    store,
    high_idle: bool = False,
    high_dwell: bool = False,
) -> DPAMetrics:
    """Generate synthetic DPA events for a transcript, compute metrics, persist, return metrics."""
    rng = random.Random(hash(transcript.id) % (2**32))
    if transcript.intended_risk_level in ("high", "critical") and not (high_idle or high_dwell):
        high_idle = rng.random() < 0.35
        high_dwell = not high_idle and rng.random() < 0.35
    call_duration_sec = _call_duration_sec(transcript)
    events = generate_synthetic_events(
        transcript.id,
        transcript.persona_id,
        call_duration_sec,
        high_idle=high_idle,
        high_dwell=high_dwell,
    )
    store.insert_dpa_events(transcript.id, events)
    metrics = compute_metrics_from_events(transcript.id, events, call_duration_sec)
    store.insert_dpa_metrics(metrics)
    return metrics
