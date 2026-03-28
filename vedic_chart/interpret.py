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
