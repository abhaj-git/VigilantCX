"""
Audit engine: evaluate transcript against persona rules, return findings with human-readable reasons.
"""
from ..config_loader import get_rules_weights
from ..data.models import Finding, Transcript

from .rules import COLLECTIONS_RULES, COLLECTIONS_POSITIVE, RAM_RULES, RAM_POSITIVE


def _get_rules_config(persona_id: str) -> tuple[dict, dict]:
    rw = get_rules_weights()
    if persona_id == "collections":
        rules = dict(rw.get("collections_rules", {}))
        positive = dict(rw.get("collections_positive_checks", {}))
        return rules, positive
    rules = dict(rw.get("ram_rules", {}))
    positive = dict(rw.get("ram_positive_checks", {}))
    return rules, positive


def _run_rule(transcript: Transcript, rule_id: str, rule_fn, config: dict) -> Finding:
    passed = rule_fn(transcript)
    c = config.get(rule_id, {})
    weight = c.get("weight")
    severity = c.get("severity", "moderate")
    reason = c.get("reason", rule_id.replace("_", " ").title())
    snippet = None
    if transcript.turns:
        snippet = transcript.turns[0].text[:200] if transcript.turns[0].text else None
    return Finding(
        id=None,
        transcript_id=transcript.id,
        rule_id=rule_id,
        passed=passed,
        severity=severity,
        reason=reason,
        snippet=snippet,
        weight=weight,
    )


def audit_transcript(transcript: Transcript) -> list[Finding]:
    """
    Run persona-specific rules on transcript. Returns list of findings (one per rule).
    Each finding has passed, severity, reason for dashboard "reason for outcome".
    """
    persona_id = transcript.persona_id
    rules_cfg, positive_cfg = _get_rules_config(persona_id)

    if persona_id == "collections":
        rule_fns = {**COLLECTIONS_RULES, **COLLECTIONS_POSITIVE}
        all_config = {**rules_cfg, **positive_cfg}
        for rid in positive_cfg:
            if "severity" not in all_config.get(rid, {}):
                all_config[rid] = {**(all_config.get(rid, {})), "severity": "low"}
    else:
        rule_fns = {**RAM_RULES, **RAM_POSITIVE}
        all_config = {**rules_cfg, **positive_cfg}
        for rid in positive_cfg:
            if "severity" not in all_config.get(rid, {}):
                all_config[rid] = {**(all_config.get(rid, {})), "severity": "low"}

    findings = []
    for rule_id, cfg in all_config.items():
        fn = rule_fns.get(rule_id)
        if not fn:
            continue
        f = _run_rule(transcript, rule_id, fn, all_config)
        findings.append(f)
    return findings
