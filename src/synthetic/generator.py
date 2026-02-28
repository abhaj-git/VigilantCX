"""
Generate synthetic transcripts from scenario config.
Produces EN/ES transcripts for Collections and RAM with greeting, body, closing and expected_findings.
"""
import uuid
from pathlib import Path

from ..data.models import Transcript, TranscriptTurn
from ..data.store import get_store
from ..config_loader import get_scenarios

from .templates import get_templates

# Map scenario traits to template block keys (greeting_*, body_*, closing_*)
TRAIT_TO_BLOCK = {
    "collections": {
        "en": {
            "greeting_with_company_and_name": "greeting_full",
            "mini_miranda": "greeting_full",
            "right_party_verification": "greeting_full",
            "full_opening": "greeting_full",
            "greeting_ok": "greeting_ok",
            "no_mini_miranda": "greeting_no_miranda_no_rpv",
            "no_rpv": "greeting_no_miranda_no_rpv",
            "skips_verification": "greeting_ok",
            "discusses_balance_early": "body_wrong_balance",
            "accurate_details": "body_accurate_recap",
            "recap_confirmation": "body_accurate_recap",
            "recap_of_arrangement": "body_accurate_recap",
            "clear_payment_options": "body_accurate_recap",
            "no_recap": "body_no_recap",
            "pushing_payment": "body_aggressive",
            "firm_to_aggressive": "body_aggressive",
            "wrong_balance_mentioned": "body_wrong_balance",
            "discusses_account_immediately": "body_no_recap",
            "discloses_to_third_party": "body_third_party_promises",
            "promises_authority": "body_third_party_promises",
            "professional_closing": "closing_recap",
            "professional_closing": "closing_recap",
        },
        "es": {
            "greeting_with_company_and_name": "greeting_full",
            "mini_miranda": "greeting_full",
            "right_party_verification": "greeting_full",
            "recap_confirmation": "body_accurate_recap",
            "greeting_ok": "greeting_ok",
            "no_recap": "body_no_recap",
            "firm_to_aggressive": "body_aggressive",
            "no_mini_miranda": "greeting_no_miranda_no_rpv",
            "no_rpv": "greeting_no_miranda_no_rpv",
            "body_accurate_recap": "body_accurate_recap",
            "body_no_recap": "body_no_recap",
            "body_aggressive": "body_aggressive",
            "closing_recap": "closing_recap",
        },
    },
    "ram": {
        "en": {
            "greeting": "greeting_full",
            "dealer_verification": "greeting_full",
            "portal_guidance": "body_portal_recap",
            "recap_next_steps": "body_portal_recap",
            "accurate_docs": "body_portal_recap",
            "confirm_understanding": "body_portal_recap",
            "professional_closing": "closing_recap",
            "greeting_ok": "greeting_ok",
            "guidance_ok": "body_portal_recap",
            "no_recap": "body_no_recap",
            "explains_but_no_confirm": "body_no_recap",
            "promises_fast_turnaround": "body_overpromise",
            "wrong_doc_list": "body_wrong_docs_bypass",
            "rushed_tone": "body_no_recap",
            "overpromise": "body_overpromise",
            "suggests_workaround": "body_wrong_docs_bypass",
            "contradicts_uw_rules": "body_contradict_uw",
            "wrong_docs": "body_wrong_docs_bypass",
            "bypass_suggestion": "body_wrong_docs_bypass",
        },
        "es": {
            "greeting": "greeting_full",
            "portal_guidance": "body_portal_recap",
            "recap": "body_portal_recap",
            "no_recap": "body_no_recap",
            "overpromise": "body_overpromise",
            "workaround": "body_wrong_docs_bypass",
            "contradict_rules": "body_contradict_uw",
        },
    },
}


def _pick_blocks(persona: str, lang: str, traits: list[str]) -> tuple[str, str, str]:
    """Resolve greeting, body, closing template keys from traits."""
    mapping = TRAIT_TO_BLOCK.get(persona, {}).get(lang, {})
    templates = get_templates(persona, lang)
    greeting_key = "greeting_ok"
    body_key = "body_no_recap"
    closing_key = "closing_none"

    for t in traits:
        block = mapping.get(t)
        if block:
            if block.startswith("greeting_"):
                greeting_key = block
            elif block.startswith("body_"):
                body_key = block
            elif block.startswith("closing_"):
                closing_key = block

    # Ensure we have valid keys
    if greeting_key not in templates:
        greeting_key = "greeting_ok" if "greeting_ok" in templates else list(templates.keys())[0]
    if body_key not in templates:
        body_key = "body_no_recap" if "body_no_recap" in templates else "body_accurate_recap"
    if closing_key not in templates:
        closing_key = "closing_none" if "closing_none" in templates else "closing_recap"
    return greeting_key, body_key, closing_key


def _build_turns(persona: str, lang: str, greeting_key: str, body_key: str, closing_key: str) -> list[TranscriptTurn]:
    templates = get_templates(persona, lang)
    turns = []
    seen = set()
    for key in (greeting_key, body_key, closing_key):
        block = templates.get(key, [])
        segment = "greeting" if key.startswith("greeting_") else ("closing" if key.startswith("closing_") else "body")
        for speaker, text in block:
            turns.append(TranscriptTurn(speaker=speaker, text=text, segment=segment))
    return turns


def generate_one(
    persona_id: str,
    scenario_id: str,
    scenario: dict,
    language: str,
    store=None,
) -> Transcript:
    """Generate a single transcript for the given scenario and language."""
    traits = scenario.get("traits", [])
    expected_findings = scenario.get("expected_findings", [])
    risk_level = _infer_risk_level(scenario_id)
    greeting_key, body_key, closing_key = _pick_blocks(persona_id, language, traits)
    turns = _build_turns(persona_id, language, greeting_key, body_key, closing_key)
    transcript_id = f"{scenario_id}_{uuid.uuid4().hex[:8]}"
    t = Transcript(
        id=transcript_id,
        persona_id=persona_id,
        language=language,
        intended_risk_level=risk_level,
        scenario_id=scenario_id,
        expected_findings=expected_findings,
        turns=turns,
    )
    if store:
        store.insert_transcript(t)
    return t


def _infer_risk_level(scenario_id: str) -> str:
    s = scenario_id.lower()
    if "crit" in s or "critical" in s:
        return "critical"
    if "high" in s:
        return "high"
    if "mod" in s or "moderate" in s:
        return "moderate"
    return "good"


def generate_transcripts(store=None, max_per_scenario: int = 1) -> list[Transcript]:
    """
    Generate synthetic transcripts for all scenarios (EN/ES) and persist to store.
    max_per_scenario: number of transcripts per scenario (default 1).
    """
    store = store or get_store()
    scenarios_cfg = get_scenarios()
    scenario_map = scenarios_cfg.get("scenarios", {})
    risk_levels = scenarios_cfg.get("risk_levels", ["good", "moderate", "high", "critical"])
    generated = []

    for persona_id in ("collections", "ram"):
        persona_scenarios = scenario_map.get(persona_id, {})
        for risk in risk_levels:
            for lang in ("en", "es"):
                scenario_list = (persona_scenarios.get(risk) or {}).get(lang) or []
                for scenario in scenario_list:
                    for _ in range(max_per_scenario):
                        t = generate_one(
                            persona_id=persona_id,
                            scenario_id=scenario["id"],
                            scenario=scenario,
                            language=lang,
                            store=store,
                        )
                        generated.append(t)
    return generated
