"""
Audit engine: evaluate transcript against persona rules, return findings with human-readable reasons.
Also evaluates DPA process rules (idle/dwell) when metrics are provided.
"""
from typing import Optional

from ..config_loader import get_rules_weights
from ..data.models import DPAMetrics, Finding, Transcript

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


def _audit_process_rules(transcript_id: str, dpa_metrics: DPAMetrics) -> list[Finding]:
    """Evaluate DPA process rules (idle/dwell). Idle = no screen activity; dwell = time on one screen."""
    rw = get_rules_weights()
    process_cfg = rw.get("process_rules") or {}
    findings = []
    for rule_id, cfg in process_cfg.items():
        weight = cfg.get("weight")
        severity = cfg.get("severity", "moderate")
        reason = cfg.get("reason", rule_id.replace("_", " ").title())
        passed = True
        detail = ""
        if rule_id == "high_idle_ratio":
            thresh = cfg.get("threshold_idle_ratio", 0.25)
            passed = dpa_metrics.idle_ratio <= thresh
            pct = int(dpa_metrics.idle_ratio * 100)
            detail = f" ({pct}% of call with no screen activity)"
        elif rule_id == "high_dwell":
            thresh = cfg.get("threshold_max_dwell_sec", 300)
            passed = dpa_metrics.max_dwell_sec <= thresh
            mins = dpa_metrics.max_dwell_sec / 60
            detail = f" (max {mins:.1f}m on one screen)"
        if not passed:
            reason = reason + detail
        findings.append(Finding(
            id=None,
            transcript_id=transcript_id,
            rule_id=rule_id,
            passed=passed,
            severity=severity,
            reason=reason,
            snippet=f"Idle {int(dpa_metrics.idle_ratio*100)}%; Dwell max {dpa_metrics.max_dwell_sec:.0f}s",
            weight=weight,
        ))
    return findings


def audit_transcript(transcript: Transcript, dpa_metrics: Optional[DPAMetrics] = None) -> list[Finding]:
    """
    Run persona-specific rules on transcript. If dpa_metrics is provided, also run process rules
    (high_idle_ratio, high_dwell). Returns list of findings.
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

    if dpa_metrics:
        findings.extend(_audit_process_rules(transcript.id, dpa_metrics))
    return findings
