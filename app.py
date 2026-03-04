"""
VigilantCX – Risk-based audit explorer.
Streamlit dashboard: below-threshold and critical results with reason for outcome.
"""
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import streamlit as st
from src.data.store import get_store
from src.scoring.filter import filter_actionable
from src.config_loader import get_score_threshold


def _reason_for_outcome(findings: list, severity_band: str) -> str:
    """Build a concise reason-for-outcome from findings: tone first, then compliance, then process (idle/dwell)."""
    failed = [f for f in findings if not f.passed]
    tone_rules = {"tone_too_casual", "tone_too_strict", "aggressive_or_threatening_tone"}
    process_rules = {"high_idle_ratio", "high_dwell"}
    tone_failures = [f for f in failed if f.rule_id in tone_rules]
    process_failures = [f for f in failed if f.rule_id in process_rules]
    other_failures = [f for f in failed if f.rule_id not in tone_rules and f.rule_id not in process_rules]
    band = severity_band.capitalize()
    if severity_band == "good" and not failed:
        return "Good: Professional tone; no compliance issues."
    if not failed:
        return f"{band}: No rule failures."
    parts = []
    if tone_failures:
        parts.append(tone_failures[0].reason)
    for f in other_failures[:3]:
        parts.append(f.reason)
    for f in process_failures:
        parts.append(f.reason)
    return f"{band}: " + "; ".join(parts) + ("." if not parts[-1].endswith(".") else "")


def _get_llm_keys():
    """Return (gemini_key, openai_key) from Secrets or env. Gemini is tried first."""
    import os
    gemini_key = openai_key = None
    try:
        if hasattr(st, "secrets"):
            gemini_key = (st.secrets.get("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
            openai_key = (st.secrets.get("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    except Exception:
        pass
    if not gemini_key:
        gemini_key = (os.environ.get("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not openai_key:
        openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    return gemini_key or None, openai_key or None


def _render_audit_ops(store):
    """Audit ops: volume completed yesterday/today, daily assignments, bias-aware distribution."""
    from datetime import date
    from src.audit_ops.assigner import run_daily_assignment
    from src.data.models import Auditor
    from src.scoring.filter import filter_actionable
    from src.config_loader import get_score_threshold

    st.subheader("Audit ops")
    st.caption("Volume completed and daily assignments (bias-aware distribution).")

    # Volume metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Volume completed (previous day)", store.volume_completed_yesterday())
    with col2:
        st.metric("Volume completed (today)", store.volume_completed_today())

    today = date.today().isoformat()
    auditors = store.list_auditors()

    # Manage auditors (minimal)
    with st.expander("Manage auditors"):
        for a in auditors:
            st.caption(f"**{a.name}** ({a.id})" + (f" — {a.role}" if a.role else ""))
        aid = st.text_input("Auditor ID", key="ao_auditor_id", placeholder="e.g. aud_1")
        aname = st.text_input("Name", key="ao_auditor_name", placeholder="e.g. Jane Doe")
        if st.button("Add auditor", key="ao_add_auditor") and aid.strip() and aname.strip():
            store.insert_auditor(Auditor(id=aid.strip(), name=aname.strip()))
            st.rerun()

    # Generate daily assignments
    threshold = get_score_threshold()
    all_ids = store.list_transcript_ids()
    actionable_ids = filter_actionable(all_ids, store, score_threshold=threshold, exclude_overridden=True) if all_ids else []
    if not auditors:
        st.info("Add at least one auditor above, then generate assignments.")
    else:
        if st.button("Generate daily assignments", key="ao_generate"):
            n = run_daily_assignment(store, actionable_ids, today)
            st.success(f"Created {n} assignment(s) for today.")
            st.rerun()

    # Assignments for today: each row expandable to show same data as Results (review then mark complete)
    st.markdown("---")
    st.markdown("**Today’s assignments** — Expand to review (reason, transcript, findings), then mark complete.")
    assignments = store.get_assignments_for_date(today)
    if not assignments:
        st.caption("No assignments for today. Use *Generate daily assignments* to distribute actionable transcripts.")
        return
    by_auditor = {}
    for a in assignments:
        by_auditor.setdefault(a.auditor_id, []).append(a)
    for auditor_id, list_a in sorted(by_auditor.items()):
        completed = sum(1 for a in list_a if a.status == "completed")
        st.markdown(f"**{auditor_id}** — {completed}/{len(list_a)} completed")
        for a in list_a:
            t = store.get_transcript(a.transcript_id)
            run = store.get_latest_audit_run(a.transcript_id)
            findings = store.get_findings(a.transcript_id) if t else []
            reason = (run.outcome_summary or _reason_for_outcome(findings, run.severity_band)) if run else "—"
            dpa_metrics = store.get_dpa_metrics(a.transcript_id) if t else None
            label = f"{a.transcript_id}" + (" ✓" if a.status == "completed" else " — Review & complete")
            with st.expander(label):
                if not t or not run:
                    st.caption("Transcript or audit run missing.")
                else:
                    st.markdown(f"**Reason for outcome:** {reason}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Score", f"{run.score:.1f}")
                        st.caption(f"Band: {run.severity_band}" + (" (critical)" if run.has_critical else ""))
                    with col2:
                        st.caption(f"Persona: {t.persona_id} | Lang: {t.language.upper()}")
                        if dpa_metrics:
                            st.caption(f"Idle: {int(dpa_metrics.idle_ratio*100)}% | Dwell max: {dpa_metrics.max_dwell_sec/60:.1f}m")
                    st.markdown("**Transcript**")
                    for turn in t.turns:
                        seg = f" [{turn.segment}]" if turn.segment else ""
                        st.text(f"{turn.speaker}{seg}: {turn.text}")
                    st.markdown("**Findings**")
                    for f in findings:
                        status = "✅" if f.passed else "❌"
                        st.caption(f"{status} {f.rule_id}: {f.reason} ({f.severity})")
                if a.status == "pending":
                    if st.button("Mark complete", key=f"complete_{a.id}"):
                        store.mark_assignment_completed(a.id)
                        st.rerun()


def main():
    st.set_page_config(page_title="VigilantCX Audit Explorer", layout="wide")
    store = get_store()
    threshold = get_score_threshold()

    # Sidebar: view selector + filters
    view = st.sidebar.radio("View", ["Results", "Audit ops"], index=0)
    show_all = st.sidebar.checkbox("Show all transcripts (including good/moderate)", value=False)
    persona_filter = st.sidebar.selectbox("Persona", ["All", "Collections", "RAM"], index=0)
    language_filter = st.sidebar.selectbox("Language", ["All", "EN", "ES"], index=0)
    st.sidebar.caption("Reason for outcome is from rules (tone + compliance). Optional: **Get LLM summary** on a result for an AI summary. *(Free-tier API quotas can be very low.)*")

    if view == "Audit ops":
        st.title("Risk-Based Audit Explorer")
        _render_audit_ops(store)
        return

    st.title("Risk-Based Audit Explorer")
    st.caption("Below-threshold and critical results only. Reason for outcome shown per transcript.")

    all_ids = store.list_transcript_ids()
    if not all_ids:
        st.info("No transcripts yet. Run the pipeline to generate and audit transcripts.")
        if st.button("Run pipeline (generate + audit)"):
            from src.pipeline import run_pipeline
            with st.spinner("Generating and auditing..."):
                run_pipeline(store=store, max_per_scenario=1, use_llm=False)
            st.rerun()
        return

    missing_dpa = [tid for tid in all_ids if not store.get_dpa_metrics(tid)]
    if missing_dpa and st.sidebar.button("Backfill DPA (synthetic) for existing transcripts"):
        from src.pipeline import backfill_dpa
        with st.spinner("Generating DPA and re-auditing..."):
            n = backfill_dpa(store=store)
        st.sidebar.success(f"Updated {n} transcript(s) with DPA metrics.")
        st.rerun()

    if show_all:
        actionable_ids = all_ids
    else:
        actionable_ids = filter_actionable(all_ids, store, score_threshold=threshold, exclude_overridden=True)

    for tid in actionable_ids:
        t = store.get_transcript(tid)
        if not t:
            continue
        if persona_filter != "All" and (persona_filter == "Collections" and t.persona_id != "collections" or persona_filter == "RAM" and t.persona_id != "ram"):
            continue
        if language_filter != "All" and (language_filter != t.language.upper()):
            continue

        run = store.get_latest_audit_run(tid)
        findings = store.get_findings(tid)
        if not run:
            continue

        reason = run.outcome_summary or _reason_for_outcome(findings, run.severity_band)
        overrides = store.get_overrides_for_transcript(tid)
        is_overridden = any(o.finding_id is None for o in overrides)
        dpa_metrics = store.get_dpa_metrics(tid)

        band_color = {"critical": "🔴", "high": "🟠", "moderate": "🟡", "good": "🟢"}.get(run.severity_band, "⚪")
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.subheader(f"{band_color} {t.id}")
                st.markdown(f"**Reason for outcome:** {reason}")
                if dpa_metrics:
                    st.caption(
                        f"**Idle:** {int(dpa_metrics.idle_ratio * 100)}% (no screen activity) — "
                        f"**Dwell (max):** {dpa_metrics.max_dwell_sec / 60:.1f}m (time on one screen)"
                    )
            with col2:
                st.metric("Score", f"{run.score:.1f}")
                st.caption(f"Band: {run.severity_band}" + (" (critical)" if run.has_critical else ""))
            with col3:
                st.caption(f"Persona: {t.persona_id} | Lang: {t.language.upper()}")
                st.caption(f"Intended risk: {t.intended_risk_level}")
                if is_overridden:
                    st.caption("✅ Overridden")
                # Per-result LLM summary: Gemini (preferred) or OpenAI
                gemini_key, openai_key = _get_llm_keys()
                if st.button("Get LLM summary" if not run.outcome_summary else "Regenerate summary", key=f"llm_{tid}"):
                    if not gemini_key and not openai_key:
                        st.error("Set GEMINI_API_KEY or OPENAI_API_KEY in Secrets or env.")
                    else:
                        from src.audit.llm_audit import get_llm_outcome_summary
                        with st.spinner("Generating..."):
                            try:
                                summary = get_llm_outcome_summary(
                                    t, findings, run.severity_band,
                                    api_key=openai_key, gemini_api_key=gemini_key,
                                )
                                if summary:
                                    store.update_audit_run_outcome_summary(tid, summary)
                                    st.rerun()
                                else:
                                    st.warning("No summary returned.")
                            except Exception as e:
                                st.error(str(e)[:200])

            with st.expander("View transcript and findings"):
                for turn in t.turns:
                    seg = f" [{turn.segment}]" if turn.segment else ""
                    st.text(f"{turn.speaker}{seg}: {turn.text}")
                st.markdown("---")
                st.markdown("**Findings**")
                for f in findings:
                    status = "✅" if f.passed else "❌"
                    st.caption(f"{status} {f.rule_id}: {f.reason} (severity: {f.severity})")
            st.markdown("---")

    if not show_all and not actionable_ids and all_ids:
        st.info("No below-threshold or critical transcripts. Use 'Show all transcripts' to see everything.")

    st.sidebar.caption(f"Score threshold: {threshold}. Showing {'all' if show_all else 'actionable only'}.")


if __name__ == "__main__":
    main()
