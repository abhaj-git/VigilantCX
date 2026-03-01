# VigilantCX – Risk-Based Audit Explorer

A prototype audit explorer for auto finance contact centers: synthetic call transcripts (Collections + RAM), rule-based and process (DPA) auditing, weighted scoring, and a dashboard with **reason for outcome** for every result.

---

## Features

- **Synthetic transcripts** — EN/ES, multiple risk levels (good, moderate, high, critical) for Collections and RAM personas
- **Rule-based audit** — Persona-specific compliance and tone rules with human-readable findings
- **DPA (Desktop Process Analytics)** — Synthetic screen-activity metrics: **idle time** (no screen activity) and **dwell time** (time on one screen). Process rules flag high idle or high dwell; metrics and failures appear on each audit card
- **Weighted scoring** — Aggregate score (0–100) and severity band (good / moderate / high / critical). Any **critical** finding sets the band to critical regardless of score
- **LLM outcome summaries** (optional) — Gemini first, OpenAI fallback; concise tone/compliance summary per transcript when API keys are set
- **Compliance overrides** — Mark transcripts or findings as overridden with reason and expiry
- **Streamlit dashboard** — Filter by persona/language, view actionable-only or all, expand transcript and findings, backfill DPA for existing data

---

## Setup

**Requirements:** Python 3.x, `pip`

```bash
cd VigilantCX
pip install -r requirements.txt
```

**Optional – LLM summaries:** Set at least one of `GEMINI_API_KEY` or `OPENAI_API_KEY`. The app uses Gemini first, then OpenAI (e.g. when Gemini hits free-tier quota). Without either key, rule-based reasons only.

- **Local:** Copy `.env.example` to `.env` and add your key(s). Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
- **Streamlit Cloud:** Add `GEMINI_API_KEY` and/or `OPENAI_API_KEY` in the app’s **Secrets**.

*(Free-tier quotas can be very low; the rule-based reason is always available.)*

---

## Quick start

**1. Generate and audit transcripts**

```bash
python -c "from src.pipeline import run_pipeline; run_pipeline(max_per_scenario=1)"
```

Or from the dashboard: run the app and click **Run pipeline** when no transcripts exist.

**2. Run the dashboard**

```bash
streamlit run app.py
```

- **Default view:** Transcripts with score ≥ threshold or any critical finding (actionable only).
- **Filters:** Persona (Collections / RAM), Language (EN / ES). Option to show all transcripts.
- **Per card:** Reason for outcome, score, band, DPA metrics (idle %, dwell max), optional **Get LLM summary**.
- **Backfill DPA:** If you have existing transcripts without DPA, use **Backfill DPA (synthetic) for existing transcripts** in the sidebar to add synthetic DPA and re-audit.

---

## Scoring

- **Score:** 0–100 (higher = worse). Sum of weights for failed rules, normalized.
- **Severity band:**

  | Score   | Band (when no critical finding) |
  |--------|-----------------------------------|
  | 0–24   | Good                              |
  | 25–49  | Moderate                          |
  | 50–100 | High                              |

  If **any** finding has severity **critical** (e.g. missing Mini-Miranda), the band is **Critical** regardless of score (so 37.5 or 47.5 can still be critical).

- **Dashboard threshold:** Transcripts with **score ≥ 70** or **any critical** are shown as actionable (`config/rules_weights.yaml`: `score_threshold`, `critical_always_show`).

---

## DPA (Desktop Process Analytics)

- **Idle time** — Time with no screen activity (before first event, after last event). High idle can indicate disengagement.
- **Dwell time** — Time on a single screen before switching. High dwell can indicate slowness or being stuck.

The app uses **synthetic DPA** (fake screen events per transcript). Process rules in config:

- **high_idle_ratio** — Fail if idle ratio > 25%.
- **high_dwell** — Fail if max dwell on one screen > 5 minutes.

These feed into the same score and **reason for outcome** as transcript rules. When real DPA (e.g. Verint) is available, the same metrics and rules can be driven from live events.

---

## Configuration and layout

| Path | Purpose |
|------|--------|
| `config/personas.yaml` | Personas (Collections, RAM) and failure modes |
| `config/scenarios.yaml` | Scenarios and traits per persona |
| `config/rules_weights.yaml` | Rule weights, severity, score threshold, **process_rules** (idle/dwell) |
| `data/vigilantcx.db` | SQLite: transcripts, findings, audit runs, overrides, **dpa_events**, **dpa_metrics** |

**Code layout**

- `app.py` — Streamlit dashboard
- `src/data/` — Models, store, schema (transcripts, findings, audit runs, overrides, DPA)
- `src/synthetic/` — Template-based transcript generator (EN/ES)
- `src/audit/` — Rule engine; `llm_audit.py` for optional LLM summaries
- `src/dpa/` — Synthetic DPA events and idle/dwell metrics
- `src/scoring/` — Weighted score, severity band, actionable filter
- `src/overrides/` — Override apply logic

---

## Pipeline and backfill

- **`run_pipeline(max_per_scenario=1, use_llm=False)`** — Generate transcripts, generate synthetic DPA, audit (transcript + process rules), score, persist. Set `use_llm=True` to request LLM summaries during run (uses API quota).
- **`backfill_dpa(store)`** — For transcripts without DPA (or with invalid metrics), generate synthetic DPA, re-audit (including process rules), and update score. Call from dashboard via **Backfill DPA** or from code.

---

*VigilantCX is a prototype: rule-based and synthetic DPA logic define what “good” looks like so the same behavior can be implemented with enterprise AI/tokens or real DPA feeds later.*
