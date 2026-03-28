from __future__ import annotations

from .ephemeris import BodyPos, SIGNS


def _sign_index(name: str) -> int:
    return SIGNS.index(name)


def _relation(s1: str, s2: str) -> str:
    """Coarse relationship between two signs."""
    a = _sign_index(s1)
    b = _sign_index(s2)
    k = (b - a) % 12
    if k == 0:
        return "same"
    if k in (4, 8):
        return "trine"
    if k == 6:
        return "opposition"
    if k in (5, 7):
        return "tension_6_8"
    if k in (3, 11):
        return "square"
    return "neutral"


def _blurb(rel: str, d_high: int) -> str:
    chart = "navamsa (D9)" if d_high == 9 else "dasamsa (D10)"
    if rel == "same":
        return (
            f"D1 and {chart} fall in the same sign — outer life and the {chart} "
            "layer point the same way; themes tend to reinforce each other."
        )
    if rel == "trine":
        return (
            f"D1 and {chart} relate by trine — supportive flow between visible expression "
            f"and the {chart} refinement."
        )
    if rel == "opposition":
        return (
            f"D1 and {chart} oppose — polarity between how things show vs how they mature "
            f"in {chart}; integration and balance matter."
        )
    if rel == "tension_6_8":
        return (
            f"D1 and {chart} in 6/8 style stress — growth through friction; "
            "the chart asks for conscious adjustment between layers."
        )
    if rel == "square":
        return (
            f"D1 and {chart} square — dynamic tension that can drive action if channelled."
        )
    return (
        f"D1 and {chart} in a mixed relationship — read with house lords, strength, and context."
    )


def compare_d1_dn(body: BodyPos, n: int) -> tuple[str, str]:
    """Return (one-line summary, short outcome blurb)."""
    s1 = body.sign_d1
    sn = body.vargas[n]
    rel = _relation(s1, sn)
    line = f"{body.name}: D1 **{s1}** → D{n} **{sn}** ({rel.replace('_', ' ')})"
    return line, _blurb(rel, n)


def _count_relations(bodies: list, n: int) -> dict[str, int]:
    from collections import Counter

    c: Counter[str] = Counter()
    for b in bodies:
        c[_relation(b.sign_d1, b.vargas[n])] += 1
    return dict(c)


def chart_summary_markdown(bodies: list) -> str:
    """High-level counts after D1 vs D9 and D1 vs D10 comparisons."""
    c9 = _count_relations(bodies, 9)
    c10 = _count_relations(bodies, 10)
    keys = ["same", "trine", "opposition", "tension_6_8", "square", "neutral"]
    labels = {
        "same": "same-sign",
        "trine": "trine",
        "opposition": "opposition",
        "tension_6_8": "6/8-style",
        "square": "square",
        "neutral": "other / mixed",
    }

    def fmt(c: dict) -> str:
        parts = []
        for k in keys:
            if c.get(k, 0):
                parts.append(f"**{labels[k]}**: {c[k]}")
        return ", ".join(parts) if parts else "—"

    return (
        "**D9 layer (vs D1):** " + fmt(c9) + "\n\n"
        "**D10 layer (vs D1):** " + fmt(c10)
    )


def chart_assessment_markdown(bodies: list) -> str:
    """Single assessment block (educational synthesis, not a full reading)."""
    moon = next((b for b in bodies if b.name == "Moon"), None)
    lagna = next((b for b in bodies if b.name == "Lagna"), None)
    sun = next((b for b in bodies if b.name == "Sun"), None)

    c9 = _count_relations(bodies, 9)
    c10 = _count_relations(bodies, 10)
    n = len(bodies)
    same9 = c9.get("same", 0)
    same10 = c10.get("same", 0)
    tense9 = c9.get("tension_6_8", 0) + c9.get("square", 0)
    tense10 = c10.get("tension_6_8", 0) + c10.get("square", 0)

    lines = []
    lines.append(
        "**How to read this:** The lines above compare your *rashi* placements (D1) with "
        "*navamsa* (D9, inner refinement) and *dasamsa* (D10, work and visibility). "
        "Same-sign pairs usually feel consistent; 6/8 or square pairs ask for integration."
    )

    if lagna and moon:
        lines.append(
            f"**Luminaries & rising:** Lagna falls in **{lagna.nakshatra}** pada **{lagna.pada}**; "
            f"Moon in **{moon.nakshatra}** pada **{moon.pada}** — mood, memory, and the emotional "
            "tone of the chart often carry these nakshatra themes."
        )
    if sun:
        lines.append(
            f"**Sun** in **{sun.nakshatra}** pada **{sun.pada}** colours purpose, vitality, and father-figure themes in broad strokes."
        )

    if same9 >= n * 0.4:
        lines.append(
            "**D9 pattern:** Several D1/D9 same-sign echoes — inner life and outer expression may line up "
            "in a straightforward way; still judge dignity and house lords in a full chart."
        )
    elif tense9 >= n * 0.35:
        lines.append(
            "**D9 pattern:** Several 6/8 or square-type D1/D9 pairs — inner refinement and outer life "
            "may pull in different directions until reconciled through practice and clarity."
        )
    else:
        lines.append(
            "**D9 pattern:** Mixed agreements between D1 and D9 — neither all-smooth nor all-friction; "
            "specific grahas above need individual weighting."
        )

    if same10 >= n * 0.4:
        lines.append(
            "**D10 pattern:** Strong overlap between D1 and D10 signs for many points — career and public "
            "role may mirror the rashi story closely."
        )
    elif tense10 >= n * 0.35:
        lines.append(
            "**D10 pattern:** Notable D1/D10 stress signatures — how you work and how you are seen can "
            "take extra calibration over time."
        )
    else:
        lines.append(
            "**D10 pattern:** Moderate mix — use the per-point lines to see which grahas anchor work "
            "visibility vs which ask for adjustment."
        )

    lines.append(
        "*This block is a template-style synthesis for study. It is not a substitute for a full Jyotish reading.*"
    )
    return "\n\n".join(lines)


def nakshatra_blurb(name: str, nak: str, pada: int) -> str:
    """Very short traditional keyword flavor (educational templates, not prediction)."""
    hints = {
        "Ashwini": "initiative, healing, speed",
        "Bharani": "bearing responsibility, creative restraint",
        "Krittika": "cutting clarity, purification, focus",
        "Rohini": "growth, attraction, nourishment",
        "Mrigashira": "search, curiosity, gentleness",
        "Ardra": "storm-to-calm, sharp insight",
        "Punarvasu": "return of light, renewal, teaching",
        "Pushya": "nurture, ethics, protection",
        "Ashlesha": "coils of insight, intensity, speech",
        "Magha": "lineage, authority, ceremony",
        "Purva Phalguni": "joy of union, creativity, rest",
        "Uttara Phalguni": "patronage, contract, lasting bond",
        "Hasta": "skill of hands, wit, service",
        "Chitra": "design, brilliance, one peak",
        "Swati": "independence, trade, wind-like movement",
        "Vishakha": "single-pointed goal, transformation",
        "Anuradha": "friendship, devotion, success after effort",
        "Jyeshtha": "elder energy, protection, intensity",
        "Mula": "roots, investigation, uprooting falsehood",
        "Purva Ashadha": "invincible waters, declaration, flair",
        "Uttara Ashadha": "victory later, dharma, patience",
        "Shravana": "listening, connection, tradition",
        "Dhanishta": "rhythm, wealth of fame, drumbeat",
        "Shatabhisha": "healing circle, secrets, the hundred physicians",
        "Purva Bhadrapada": "fire sacrifice, passion, depth",
        "Uttara Bhadrapada": "serpent of the deep, stability, wisdom",
        "Revati": "nourishing journey, closure, protection",
    }
    base = hints.get(nak, "study this nakshatra’s deity, symbol, and shakti in your tradition.")
    return f"**{name}** in **{nak}** pada **{pada}** — *{base}*"
