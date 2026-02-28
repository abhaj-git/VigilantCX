# VigilantCX – Risk-Based Audit Explorer

Auto finance contact center audit explorer: synthetic transcripts (Collections + RAM), weighted audit scoring, compliance overrides, and a dashboard showing only below-threshold or critical results with **reason for outcome**.

## Setup

```bash
cd VigilantCX
pip install -r requirements.txt
```

**Optional – LLM outcome summaries:** Set `OPENAI_API_KEY` in your environment to get concise, NLP-based reason-for-outcome summaries (tone, intent, compliance from full transcript). Without it, the app uses rule-based reasons only.

## Run pipeline (generate + audit)

Generate synthetic transcripts (EN/ES, good/moderate/high/critical) for Collections and RAM personas, run the audit engine, and persist scores:

```bash
python -c "from src.pipeline import run_pipeline; run_pipeline(max_per_scenario=1)"
```

Or from the dashboard: open the app and click **Run pipeline** when no transcripts exist.

## Dashboard

```bash
streamlit run app.py
```

- **Default view**: Only below-threshold or critical transcripts.
- **Reason for outcome**: Each card shows an LLM-generated concise summary (tone, compliance, intent from full text) when `OPENAI_API_KEY` is set; otherwise the rule-based reason list.
- **Filters**: Persona (Collections / RAM), Language (EN / ES). Option to show all transcripts.
- **Expand**: View full transcript and per-rule findings.

## Layout

- `config/` – Personas, scenarios, rule weights, score threshold.
- `src/data/` – SQLite store, transcript/finding/override models.
- `src/synthetic/` – Template-based transcript generator (EN/ES).
- `src/audit/` – Rule engine; `llm_audit.py` for LLM-based tone/compliance/summary.
- `src/scoring/` – Weighted score, severity band, filter.
- `src/overrides/` – Compliance override apply logic.
- `app.py` – Streamlit dashboard.

Data is stored in `data/vigilantcx.db`.
