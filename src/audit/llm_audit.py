"""
LLM-based audit: judge tone, intent, and compliance from full transcript text.
Supports Gemini (preferred, free tier) or OpenAI. Produces a concise outcome summary.
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


def _build_prompt(transcript: Transcript, findings: list[Finding], severity_band: str) -> str:
    text = _transcript_to_text(transcript)
    persona = "Collections (regulated collections agent, customer call)" if transcript.persona_id == "collections" else "RAM (dealer relationship / inside sales, dealer call)"
    findings_ctx = _findings_context(findings, severity_band)
    return f"""You are a compliance auditor for an auto finance contact center. Below is a call transcript (persona: {persona}) and the rule-based audit result.

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
"""[:12000]


def _call_gemini(prompt: str, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
    except ImportError:
        return None
    key = (api_key or "").strip().strip('"').strip("'")
    if not key:
        return None
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    if not resp or not getattr(resp, "text", None):
        return None
    return resp.text.strip()


def _call_openai(prompt: str, api_key: str) -> Optional[str]:
    try:
        import openai
    except ImportError:
        return None
    key = (api_key or "").strip().strip('"').strip("'")
    if not key:
        return None
    client = openai.OpenAI(api_key=key, timeout=60.0)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.3,
    )
    summary = (resp.choices[0].message.content or "").strip()
    return summary or None


def get_llm_outcome_summary(
    transcript: Transcript,
    findings: list[Finding],
    severity_band: str,
    api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Call LLM (Gemini preferred, else OpenAI) to get a concise reason-for-outcome summary.
    Uses GEMINI_API_KEY first if set, then OPENAI_API_KEY. Pass gemini_api_key or api_key to override.
    """
    gemini_key = (gemini_api_key or os.environ.get("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    openai_key = (api_key or os.environ.get("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key and not openai_key:
        return None

    prompt = _build_prompt(transcript, findings, severity_band)
    summary = None
    err = None

    if gemini_key:
        try:
            summary = _call_gemini(prompt, gemini_key)
        except Exception as e:
            err = e
    if summary:
        return summary

    if openai_key:
        try:
            summary = _call_openai(prompt, openai_key)
        except Exception as e:
            err = e
    if summary:
        return summary

    if err:
        msg = str(err).strip()
        if "429" in msg or "rate" in msg.lower():
            raise ValueError("API rate limit. Wait a minute and try again.")
        if "401" in msg or "invalid" in msg.lower() or "API key" in msg:
            raise ValueError("Invalid API key. Check GEMINI_API_KEY or OPENAI_API_KEY in Secrets or env.")
        raise
    return None
