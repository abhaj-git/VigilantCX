"""
Detailed D1→D9 and D1→D10 copy: planet + destination sign in the varga, in plain language.
Overrides include user-provided D10 lines; the rest use sign + planet templates.
"""
from __future__ import annotations

from .ephemeris import BodyPos, SIGNS

# --- Your exact D10 examples (planet → sign in D10) ---------------------------
_D10_OVERRIDE: dict[tuple[str, str], str] = {
    ("Sun", "Leo"): (
        "Very strong for career visibility, authority, leadership identity."
    ),
    ("Venus", "Taurus"): (
        "Venus gets more stable and comfortable here. Good for value creation, refinement, appeal, "
        "support from networks."
    ),
    ("Jupiter", "Pisces"): (
        "Strong spiritual/intuitive wisdom in career. Can give guidance, strategy, advisory quality."
    ),
    ("Saturn", "Aquarius"): (
        "Very karmic placement for structured large-scale work, systems, institutions, responsibility."
    ),
    ("Mercury", "Scorpio"): (
        "Sharp mind in work, but deeper, investigative, political, strategic communication style."
    ),
    ("Rahu", "Scorpio"): (
        "Career can involve intensity, power struggles, transformation, hidden currents, obsession with "
        "control/results."
    ),
}

# Career / public layer — what the *destination* sign in D10 tends to emphasize
_D10_SIGN: dict[str, str] = {
    "Aries": "Pioneering roles, competition, being first in the door, visible initiative.",
    "Taurus": "Building tangible value, stability, aesthetics, comfort, and steady income or patronage.",
    "Gemini": "Messaging, analysis, variety, teaching bits, networking, and adaptable skill at work.",
    "Cancer": "Care, protection, people-facing sensitivity, “home base” roles, or public mood.",
    "Leo": "Visibility, authority, creative leadership, and being seen as central to the mission.",
    "Virgo": "Craft, correction, service, systems detail, and reputations built on competence.",
    "Libra": "Partnership at work, design, diplomacy, clients, and balance between sides.",
    "Scorpio": "Intensity, investigation, strategy, crisis handling, power dynamics, and deep change.",
    "Sagittarius": "Teaching, counsel, big-picture mission, travel or cross-cultural work, belief-led roles.",
    "Capricorn": "Hierarchy, duty, long climbs, institutions, seniority, and earned status.",
    "Aquarius": "Systems, collectives, innovation at scale, institutions, and responsibility to a group.",
    "Pisces": "Intuition, healing, imagination, charity, or work that dissolves rigid boundaries.",
}

# Inner / partnership (navamsa) layer — destination sign in D9
_D9_SIGN: dict[str, str] = {
    "Aries": "Inner life wants honesty, courage, and a fresh start in how you commit or soften.",
    "Taurus": "Seeks loyalty, sensual steadiness, and emotional safety in relationship and self-worth.",
    "Gemini": "Needs conversation, curiosity, and mental match; inner story can feel split until integrated.",
    "Cancer": "Deep nesting, protection of bonds, family tone in love, and mood as a compass.",
    "Leo": "Heart, dignity, and warmth in love; pride and generosity shape the subtle self.",
    "Virgo": "Refinement, service, and discernment in intimacy; love grows through small true acts.",
    "Libra": "Balance, contract, and beauty in partnership; fairness becomes a spiritual lesson.",
    "Scorpio": "All-in bonding, trust tests, transformation through intimacy, and emotional truth.",
    "Sagittarius": "Freedom-within-faith, growth through partner, and honesty about beliefs.",
    "Capricorn": "Commitment as duty and time; love matures through patience and integrity.",
    "Aquarius": "Friendship-in-love, space, and shared ideals; unconventional loyalty.",
    "Pisces": "Surrender, compassion, and merging tides; boundaries are the gentle teacher.",
}

# Short planet flavor for D10 (work / reputation)
_D10_PLANET: dict[str, str] = {
    "Lagna": "How you are met and how you step into responsibility publicly",
    "Sun": "Authority, recognition, and what you stand for at work",
    "Moon": "Public mood, care, needs, and what must feel safe to perform well",
    "Mars": "Drive, debate, technical fight, and where you push for results",
    "Mercury": "Skill, speech, deals, analysis, and craft in the role",
    "Jupiter": "Guidance, teaching, ethics, and expansion visible in the job",
    "Venus": "Alliances, value, comfort, art, and reward through people or design",
    "Saturn": "Time, structure, seniority, and the hard parts you still show up for",
    "Rahu": "Hungry edge, niche, foreign or unusual threads in the career story",
    "Ketu": "Letting go of titles, research, or working from the side-lines with skill",
}

# Short planet flavor for D9 (inner / partnership tone)
_D9_PLANET: dict[str, str] = {
    "Lagna": "How the subtle self and body-soul story want to mature in love and trust",
    "Sun": "Core pride and father/authority themes in the inner marriage of life",
    "Moon": "Emotional home, mothering patterns, and what intimacy must nourish",
    "Mars": "Passion, courage, and conflict style inside close bonds",
    "Mercury": "Friendship-in-love, words, and the mind’s role in commitment",
    "Jupiter": "Faith, children, teaching, and what expands the heart in partnership",
    "Venus": "Romance, pleasure, art of loving, and what you attract in the subtle chart",
    "Saturn": "Vows, delay, seriousness, and karma in relationship timing",
    "Rahu": "Craving, fascination, and unusual scripts in intimacy",
    "Ketu": "Release, spiritual friendship, and what you stop chasing in love",
}


def _paragraph_d10(body: BodyPos) -> str:
    p = body.name
    dest = body.vargas[10]
    o = _D10_OVERRIDE.get((p, dest))
    if o:
        return o
    sign_line = _D10_SIGN.get(dest, "the career and reputation side of life.")
    planet_line = _D10_PLANET.get(p, "This factor")
    return (
        f"{planet_line} lands in **{dest}** for D10: {sign_line} "
        f"Read houses and strength for the full job story."
    )


def _paragraph_d9(body: BodyPos) -> str:
    p = body.name
    dest = body.vargas[9]
    sign_line = _D9_SIGN.get(dest, "the inner and partnership refinement of the chart.")
    planet_line = _D9_PLANET.get(p, "This factor")
    return (
        f"{planet_line} ripens in **{dest}** in navamsa: {sign_line} "
        f"Use the full chart for houses and dignity."
    )


def varga_detail_block(body: BodyPos, n: int) -> str:
    """
    One block: header line + blank line + interpretive paragraph for D9 or D10.
    """
    if n not in (9, 10):
        raise ValueError("n must be 9 or 10")
    dest = body.vargas[n]
    d1 = body.sign_d1
    header = f"**{body.name}** {d1} → **{dest}** in D{n}"
    body_text = _paragraph_d9(body) if n == 9 else _paragraph_d10(body)
    return f"{header}\n\n{body_text}"


def varga_detail_intro(n: int) -> str:
    if n == 9:
        return (
            "**D1 → D9 (navamsa)** — inner tone, partnership and subtle self. "
            "Each block: rashi sign → navamsa sign, then what that movement suggests in simple language."
        )
    return (
        "**D1 → D10 (dasamsa)** — work, visibility, how effort becomes reputation. "
        "Each block: rashi sign → dasamsa sign, then a plain reading for that graha."
    )
