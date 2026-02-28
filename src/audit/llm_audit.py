"""
LLM-based audit: judge tone, intent, and compliance from full transcript text.
Produces a concise outcome summary for the dashboard.
"""
import os
from typing import Optional

from ..data.models import Finding, Transcript


def _transcript_to_text(t: Transcript) -> str:
    lines = []
    for turn in t.turns:
        seg = f" [{turn.segment}]" if turn.segment else ""
        lines.append(f"{turn.speaker}{seg}: {turn.text}")
    return "\n".join(lines)


def _findings_context(findings: list[Finding], severity_band: str) -> str:
    failed = [f for f in findings if not f.passed]
    if not failed:
        return f"Rule-based result: {severity_band}. No rule failures."
    parts = [f.reason for f in failed]
    return f"Rule-based result: {severity_band}. Failed checks: {'; '.join(parts)}"


def get_llm_outcome_summary(
    transcript: Transcript,
    findings: list[Finding],
    severity_band: str,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Call LLM to assess tone, intent, compliance from full text and return a concise
    (1-2 sentence) reason-for-outcome summary. Returns None if no API key or on error.
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        import openai
    except ImportError:
        return None

    client = openai.OpenAI(api_key=api_key)
    text = _transcript_to_text(transcript)
    persona = "Collections (regulated collections agent, customer call)" if transcript.persona_id == "collections" else "RAM (dealer relationship / inside sales, dealer call)"
    findings_ctx = _findings_context(findings, severity_band)

    prompt = f"""You are a compliance auditor for an auto finance contact center. Below is a call transcript (persona: {persona}) and the rule-based audit result.

Rule-based result context: {findings_ctx}

Transcript:
---
{text}
---

Using the full transcript, assess:
1. **Tone guardrails** (required): Was the agent too casual with the customer/dealer (e.g. slang, overly friendly, unprofessional) or too strict (e.g. harsh, cold, intimidating, threatening)? If tone is appropriate (professional, empathetic but firm), say so briefly.
2. Compliance: disclosures, verification, recap as relevant.
3. Write a concise 1-2 sentence "reason for outcome" summary for the dashboard. Start with the severity band ({severity_band}). Always include tone: call out "too casual" or "too strict" when present; otherwise note "tone appropriate" or "professional tone". Then add compliance points (e.g. missing Mini-Miranda, good recap). Be specific and brief.

Respond with ONLY the 1-2 sentence summary, no labels or bullet points. Examples:
- "Moderate: Tone too casual; no recap of arrangement."
- "High: Tone too strict and pushy; no verification before discussing account."
- "Good: Professional tone, full verification, clear recap."
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3,
        )
        summary = (resp.choices[0].message.content or "").strip()
        return summary if summary else None
    except Exception as e:
        raise  # so caller can show API/auth errors
