"""
VigilantCX – Risk-based audit explorer.
Streamlit dashboard: below-threshold and critical results with reason for outcome.
"""
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src.data.store import get_store
from src.scoring.filter import filter_actionable
from src.config_loader import get_score_threshold


def _reason_for_outcome(findings: list, severity_band: str) -> str:
    """Build human-readable reason for outcome from findings."""
    failed = [f for f in findings if not f.passed]
    passed_important = [f for f in findings if f.passed and f.severity in ("critical", "high", "moderate")]
    if severity_band == "good" and not failed:
        if passed_important:
            return "Good: " + "; ".join(f.reason for f in passed_important[:3])
        return "Good: No compliance issues identified."
    if not failed:
        return severity_band.capitalize() + ": No failures; score band from aggregate."
    parts = [f.reason for f in failed]
    return severity_band.capitalize() + ": " + "; ".join(parts)


def main():
    st.set_page_config(page_title="VigilantCX Audit Explorer", layout="wide")
    st.title("Risk-Based Audit Explorer")
    st.caption("Below-threshold and critical results only. Reason for outcome shown per transcript.")

    store = get_store()
    threshold = get_score_threshold()

    show_all = st.sidebar.checkbox("Show all transcripts (including good/moderate)", value=False)
    persona_filter = st.sidebar.selectbox("Persona", ["All", "Collections", "RAM"], index=0)
    language_filter = st.sidebar.selectbox("Language", ["All", "EN", "ES"], index=0)

    if st.sidebar.button("Add LLM summaries to existing runs"):
        import os
        # Key from Streamlit Secrets (Cloud) or environment (local)
        api_key = None
        try:
            if hasattr(st, "secrets") and st.secrets.get("OPENAI_API_KEY"):
                api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.sidebar.error(
                "OPENAI_API_KEY not found. "
                "Local: In the same terminal run 'export OPENAI_API_KEY=\"sk-...\"' then stop Streamlit (Ctrl+C) and start it again with 'streamlit run app.py'. "
                "Cloud: Add OPENAI_API_KEY in app Settings → Secrets."
            )
        else:
            from src.pipeline import backfill_llm_summaries
            with st.spinner("Calling LLM for each transcript..."):
                n, err = backfill_llm_summaries(store=store, api_key=api_key)
            if n == 0:
                if err:
                    st.sidebar.error(f"API error: {err[:200]}")
                else:
                    st.sidebar.warning(
                        "Updated 0 transcripts. On Streamlit Cloud: run **Run pipeline** first (same session), then this button. Or check API key and credits."
                    )
            else:
                st.sidebar.success(f"Updated {n} transcripts with LLM summaries.")
            st.rerun()

    all_ids = store.list_transcript_ids()
    if not all_ids:
        st.info("No transcripts yet. Run the pipeline to generate and audit transcripts.")
        if st.button("Run pipeline (generate + audit)"):
            from src.pipeline import run_pipeline
            with st.spinner("Generating and auditing..."):
                run_pipeline(store=store, max_per_scenario=1)
            st.rerun()
        return

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

        band_color = {"critical": "🔴", "high": "🟠", "moderate": "🟡", "good": "🟢"}.get(run.severity_band, "⚪")
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.subheader(f"{band_color} {t.id}")
                st.markdown(f"**Reason for outcome:** {reason}")
            with col2:
                st.metric("Score", f"{run.score:.1f}")
                st.caption(f"Band: {run.severity_band}" + (" (critical)" if run.has_critical else ""))
            with col3:
                st.caption(f"Persona: {t.persona_id} | Lang: {t.language.upper()}")
                st.caption(f"Intended risk: {t.intended_risk_level}")
                if is_overridden:
                    st.caption("✅ Overridden")

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
