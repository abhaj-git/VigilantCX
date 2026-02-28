"""
Rule checkers: take full transcript text (and optional segments) and return pass/fail for each rule.
Rule IDs and metadata come from config; here we implement the detection logic.
"""
import re
from ..data.models import Transcript, TranscriptTurn


def _full_text(t: Transcript) -> str:
    return " ".join(turn.text for turn in t.turns).lower()


def _agent_text(t: Transcript, segment: str | None = None) -> str:
    parts = [turn.text for turn in t.turns if turn.speaker == "agent" and (segment is None or turn.segment == segment)]
    return " ".join(parts).lower()


def _has_phrase(text: str, *phrases: str) -> bool:
    text = text.lower()
    return any(p.lower() in text for p in phrases)


# --- Collections rules (failure = present when bad, or absent when required) ---

COLLECTIONS_MINI_MIRANDA_PHRASES = [
    "collect a debt",
    "collect a debt",
    "attempt to collect",
    "cobrar una deuda",
    "comunicación para cobrar",
]

def collections_mini_miranda(t: Transcript) -> bool:
    """Pass if Mini-Miranda (or Spanish equivalent) is present in greeting."""
    agent_greeting = _agent_text(t, "greeting")
    return _has_phrase(agent_greeting, *COLLECTIONS_MINI_MIRANDA_PHRASES)


def collections_right_party_verification(t: Transcript) -> bool:
    """Pass if agent asks for verification (last 4 SSN, DOB, etc.) before discussing balance."""
    agent_greeting = _agent_text(t, "greeting")
    return _has_phrase(agent_greeting, "last four", "social", "date of birth", "dob", "verify", "confirm", "últimos cuatro", "seguro social", "verificar", "confirmar")


def collections_no_account_before_verify(t: Transcript) -> bool:
    """Pass if account/balance is not discussed in greeting (i.e. verification first)."""
    agent_greeting = _agent_text(t, "greeting")
    # If greeting contains balance/past due/account number discussed as fact, fail
    if _has_phrase(agent_greeting, "balance is", "past due", "you're past due", "saldo es", "días de atraso"):
        return False
    return True


def collections_has_recap(t: Transcript) -> bool:
    """Pass if closing contains recap (confirm, summary, payment date/amount)."""
    agent_closing = _agent_text(t, "closing")
    return _has_phrase(agent_closing, "confirm", "recap", "to summarize", "payment", "due", "confirmar", "resumen", "pago", "fecha")


def collections_no_aggressive_tone(t: Transcript) -> bool:
    """Pass if no aggressive/threatening language."""
    agent_all = _agent_text(t)
    bad = ["repossession", "repo", "we're sending", "pay now", "don't miss it", "what are you going to do", "no falle", "enviamos a recuperación"]
    return not _has_phrase(agent_all, *bad)


def collections_accurate_balance(t: Transcript) -> bool:
    """Pass if no obvious misstatement (we can't verify numbers; look for conflict or 'I thought')."""
    full = _full_text(t)
    # Customer questioning balance suggests possible misstatement
    if _has_phrase(full, "i thought it was", "pensé que era", "thought it was"):
        return False
    return True


def collections_no_third_party_disclosure(t: Transcript) -> bool:
    """Pass if agent doesn't disclose account to third party (calling for someone else)."""
    full = _full_text(t)
    if _has_phrase(full, "calling for my", "calling for his", "calling for her", "llamo por mi hermano", "can you tell me what he owes"):
        agent = _agent_text(t)
        if _has_phrase(agent, "owe", "balance", "account", "debe", "saldo", "cuenta"):
            return False
    return True


def collections_no_promise_outside_authority(t: Transcript) -> bool:
    """Pass if agent doesn't promise waive/special treatment without verification."""
    agent = _agent_text(t)
    if _has_phrase(agent, "waive", "waive some fees", "I might be able to", "exception"):
        return False
    return True


# --- RAM rules ---

RAM_VERIFY_PHRASES = ["dealer id", "dealer ID", "confirm", "ID del concesionario", "confirma"]

def ram_has_greeting(t: Transcript) -> bool:
    agent = _agent_text(t, "greeting")
    return _has_phrase(agent, "this is", "speaking", "soy", "con ", "hablo")


def ram_dealer_verification(t: Transcript) -> bool:
    agent_greeting = _agent_text(t, "greeting")
    return _has_phrase(agent_greeting, *RAM_VERIFY_PHRASES)


def ram_has_recap(t: Transcript) -> bool:
    agent_closing = _agent_text(t, "closing")
    return _has_phrase(agent_closing, "next step", "summarize", "confirm", "resumen", "próximo", "document", "stip", "upload")


def ram_no_policy_bypass(t: Transcript) -> bool:
    agent = _agent_text(t)
    bad = ["work around", "workaround", "skip", "omit", "exception", "we've made exceptions", "excepciones", "omitir", "podemos saltarnos"]
    return not _has_phrase(agent, *bad)


def ram_no_contradict_underwriting(t: Transcript) -> bool:
    agent = _agent_text(t)
    bad = ["they say that but", "we've approved higher", "push it through", "underwriting usually wants but"]
    return not _has_phrase(agent, *bad)


def ram_correct_documentation(t: Transcript) -> bool:
    """Pass if not giving wrong doc guidance or bypass."""
    return ram_no_policy_bypass(t)


def ram_no_overpromise_turnaround(t: Transcript) -> bool:
    agent = _agent_text(t)
    # "end of day", "today", "by tomorrow" without qualifier
    if _has_phrase(agent, "end of day today", "by today", "hoy mismo", "para hoy"):
        return False
    return True


def ram_confirmation_of_understanding(t: Transcript) -> bool:
    agent = _agent_text(t)
    return _has_phrase(agent, "did that work", "do you see", "got it", "understand", "¿le apareció", "¿funciona", "entendió")


def ram_no_transactional_tone(t: Transcript) -> bool:
    """Pass if not overly brief/rushed (no 'okay bye' only)."""
    agent_closing = _agent_text(t, "closing")
    if len(agent_closing.strip()) < 20 and _has_phrase(agent_closing, "bye", "adiós", "okay"):
        return False
    return True


# --- Tone guardrails (both personas): too casual vs too strict ---

def tone_not_too_casual(t: Transcript) -> bool:
    """Pass if agent avoids unprofessional/casual language with customer or dealer."""
    agent = _agent_text(t)
    casual = ["hey ", " hey,", "dude", "yeah man", "no worries", "gonna", "wanna", "gotta", "kinda", "sorta", "okay so", "cool ", "awesome", "totally", "super ", "oh man", "dang", "yep ", "yup ", "nope ", "sure thing", "no problemo", "de nada", "tranquilo", "dale "]
    return not _has_phrase(agent, *casual)


def tone_not_too_strict(t: Transcript) -> bool:
    """Pass if agent avoids harsh, cold, or intimidating language."""
    agent = _agent_text(t)
    strict = ["you need to", "you must", "right now", "no excuses", "don't waste my", "listen here", "you have to", "or else", "last chance", "no ifs", "no buts", "tiene que", "debe ", "ahora mismo", "sin excusas"]
    return not _has_phrase(agent, *strict)


# Rule function registry by persona. Each returns True if transcript PASSES (good), False if fails.
COLLECTIONS_RULES = {
    "missing_mini_miranda": collections_mini_miranda,
    "no_verification_before_discussing_account": lambda t: collections_right_party_verification(t) and collections_no_account_before_verify(t),
    "no_recap_of_arrangement": collections_has_recap,
    "aggressive_or_threatening_tone": collections_no_aggressive_tone,
    "misstating_balance_or_fees": collections_accurate_balance,
    "third_party_disclosure_violation": collections_no_third_party_disclosure,
    "promising_outside_policy_authority": collections_no_promise_outside_authority,
    "improper_handling_of_disputes": lambda t: True,
    "tone_too_casual": tone_not_too_casual,
    "tone_too_strict": tone_not_too_strict,
}

COLLECTIONS_POSITIVE = {
    "has_greeting": lambda t: _has_phrase(_agent_text(t, "greeting"), "thank you", "calling", "gracias", "llamar"),
    "has_recap": collections_has_recap,
    "has_right_party_verification": collections_right_party_verification,
}

RAM_RULES = {
    "advising_policy_bypass": ram_no_policy_bypass,
    "contradicting_underwriting_rules": ram_no_contradict_underwriting,
    "incorrect_documentation_guidance": ram_correct_documentation,
    "overpromising_turnaround_time": ram_no_overpromise_turnaround,
    "no_confirmation_of_understanding": ram_confirmation_of_understanding,
    "no_recap": ram_has_recap,
    "transactional_tone_harming_relationship": ram_no_transactional_tone,
    "tone_too_casual": tone_not_too_casual,
    "tone_too_strict": tone_not_too_strict,
}

RAM_POSITIVE = {
    "has_greeting": ram_has_greeting,
    "has_dealer_verification": ram_dealer_verification,
    "has_recap": ram_has_recap,
}
