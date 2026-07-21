"""
Weighted scoring: aggregate findings into a single score and severity band.
Score 0 = best, higher = worse. Normalized to 0-100 for display (100 = worst).
"""
from ..data.models import Finding

# Max possible penalty from weights (approximate cap for normalization)
DEFAULT_MAX_WEIGHT_SUM = 200


def score_findings(findings: list[Finding], max_weight_sum: float = DEFAULT_MAX_WEIGHT_SUM) -> tuple[float, str, bool]:
    """
    Aggregate findings into score (0-100, higher = worse), severity_band, and has_critical.
    Failed rules add their weight; passed rules don't.
    """
    total_penalty = 0.0
    has_critical = False
    for f in findings:
        if not f.passed and f.weight is not None:
            total_penalty += f.weight
        if not f.passed and f.severity == "critical":
            has_critical = True

    # Normalize to 0-100 (min 0, max 100)
    raw_score = min(total_penalty, max_weight_sum)
    score_0_100 = (raw_score / max_weight_sum) * 100 if max_weight_sum else 0

    band = severity_band_from_score(score_0_100, has_critical)
    return round(score_0_100, 1), band, has_critical


def severity_band_from_score(score_0_100: float, has_critical: bool) -> str:
    """Map score and critical flag to band: good, moderate, high, critical."""
    if has_critical or score_0_100 >= 50:
        return "critical" if has_critical else "high"
    if score_0_100 >= 25:
        return "moderate"
    return "good"
