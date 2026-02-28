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
    """Build a concise reason-for-outcome from findings: tone first, then compliance. No API."""
    failed = [f for f in findings if not f.passed]
    tone_rules = {"tone_too_casual", "tone_too_strict", "aggressive_or_threatening_tone"}
    tone_failures = [f for f in failed if f.rule_id in tone_rules]
    other_failures = [f for f in failed if f.rule_id not in tone_rules]
    # Build one short sentence: severity + tone (if any) + other
    band = severity_band.capitalize()
    if severity_band == "good" and not failed:
        return "Good: Professional tone; no compliance issues."
    if not failed:
        return f"{band}: No rule failures."
    parts = []
    if tone_failures:
        parts.append(tone_failures[0].reason)  # e.g. "Tone too casual with customer"
    for f in other_failures[:3]:  # max 3 other reasons
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


def main():
    st.set_page_config(page_title="VigilantCX Audit Explorer", layout="wide")
    st.title("Risk-Based Audit Explorer")
    st.caption("Below-threshold and critical results only. Reason for outcome shown per transcript.")

    store = get_store()
    threshold = get_score_threshold()

    show_all = st.sidebar.checkbox("Show all transcripts (including good/moderate)", value=False)
    persona_filter = st.sidebar.selectbox("Persona", ["All", "Collections", "RAM"], index=0)
    language_filter = st.sidebar.selectbox("Language", ["All", "EN", "ES"], index=0)

    st.sidebar.caption("Reason for outcome is from rules (tone + compliance). Optional: **Get LLM summary** on a result for an AI summary.")

    all_ids = store.list_transcript_ids()
    if not all_ids:
        st.info("No transcripts yet. Run the pipeline to generate and audit transcripts.")
        if st.button("Run pipeline (generate + audit)"):
            from src.pipeline import run_pipeline
            with st.spinner("Generating and auditing..."):
                run_pipeline(store=store, max_per_scenario=1, use_llm=False)
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
