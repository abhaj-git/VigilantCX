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


# Short tags — one phrase each, no repeated chart lectures in every caption
_GRAHA_TAG = {
    "Lagna": "rising / body",
    "Sun": "self & father",
    "Moon": "mind & mother",
    "Mars": "drive & conflict",
    "Mercury": "speech & skill",
    "Jupiter": "guidance & growth",
    "Venus": "love & comfort",
    "Saturn": "duty & time",
    "Rahu": "hunger & odd paths",
    "Ketu": "letting go & insight",
}


def _blurb(body: BodyPos, rel: str, d_high: int) -> str:
    """One plain sentence: what is different for this graha only."""
    dn = "D9" if d_high == 9 else "D10"
    g = body.name
    tag = _GRAHA_TAG.get(g, g)
    if rel == "same":
        return f"**{g}** ({tag}): rashi and {dn} use the **same sign** — one thread, no split between layers."
    if rel == "trine":
        return f"**{g}** ({tag}): rashi and {dn} **trine** — same element, easy backup; not the same sign."
    if rel == "opposition":
        return f"**{g}** ({tag}): rashi and {dn} **oppose** — two ends to balance; neither cancels the other."
    if rel == "tension_6_8":
        return f"**{g}** ({tag}): rashi and {dn} in a **6/8** link — one side has to grow to feed the other."
    if rel == "square":
        return f"**{g}** ({tag}): rashi and {dn} **square** — push/pull; usually needs a clear choice or habit."
    return f"**{g}** ({tag}): rashi and {dn} in a **mixed** link — small shift, not a headline clash."


_REL_LABEL = {
    "same": "same sign",
    "trine": "trine",
    "opposition": "opposition",
    "tension_6_8": "6 / 8 stress",
    "square": "square",
    "neutral": "mixed",
}


def compare_d1_dn(body: BodyPos, n: int) -> tuple[str, str]:
    """Return (one-line summary, meaningful blurb)."""
    s1 = body.sign_d1
    sn = body.vargas[n]
    rel = _relation(s1, sn)
    label = _REL_LABEL.get(rel, rel)
    line = f"{body.name}: D1 **{s1}** → D{n} **{sn}** ({label})"
    return line, _blurb(body, rel, n)


def _count_relations(bodies: list, n: int) -> dict[str, int]:
    from collections import Counter

    c: Counter[str] = Counter()
    for b in bodies:
        c[_relation(b.sign_d1, b.vargas[n])] += 1
    return dict(c)


def chart_summary_markdown(bodies: list) -> str:
    """Counts only — no repeated prose (details stay in each row + quick lists below)."""
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

    return "**D9 (rashi vs navamsa):** " + fmt(c9) + "\n\n**D10 (rashi vs dasamsa):** " + fmt(c10)


def layer_comparison_narrative(bodies: list, n: int) -> str:
    """Name-only roll call: who matches, who stresses — no repeated theory."""
    assert n in (9, 10)
    dn = f"D{n}"
    same = [b.name for b in bodies if b.sign_d1 == b.vargas[n]]
    trn = [b.name for b in bodies if _relation(b.sign_d1, b.vargas[n]) == "trine"]
    opp = [b.name for b in bodies if _relation(b.sign_d1, b.vargas[n]) == "opposition"]
    hard = [
        b.name
        for b in bodies
        if _relation(b.sign_d1, b.vargas[n]) in ("tension_6_8", "square")
    ]
    lines = []
    if same:
        lines.append(f"**Same rashi & {dn}:** {', '.join(same)}.")
    if trn:
        lines.append(f"**Trine only:** {', '.join(trn)}.")
    if opp:
        lines.append(f"**Opposite:** {', '.join(opp)}.")
    if hard:
        lines.append(f"**6/8 or square:** {', '.join(hard)}.")
    if not lines:
        return f"No grahas repeat the rashi sign in {dn}; every row above shows where that layer shifts."
    return "\n".join(lines)


def chart_assessment_markdown(bodies: list) -> str:
    """At most one plain skew line per layer, else a single neutral line. No echo of captions."""
    c9 = _count_relations(bodies, 9)
    c10 = _count_relations(bodies, 10)
    n = len(bodies)
    easy9 = c9.get("same", 0) + c9.get("trine", 0)
    easy10 = c10.get("same", 0) + c10.get("trine", 0)
    hard9 = c9.get("tension_6_8", 0) + c9.get("square", 0)
    hard10 = c10.get("tension_6_8", 0) + c10.get("square", 0)

    lines = []
    if easy9 >= n * 0.65:
        lines.append("Most grahas agree between rashi and D9 (same or trine).")
    elif hard9 >= n * 0.5:
        lines.append("Several grahas stress between rashi and D9 — those names are worth a second look.")

    if easy10 >= n * 0.65:
        lines.append("Most grahas agree between rashi and D10 (same or trine).")
    elif hard10 >= n * 0.5:
        lines.append("Several grahas stress between rashi and D10 — work-life story may not match birth-chart signs line by line.")

    if not lines:
        lines.append("No one blanket pattern wins; trust the row-by-row notes and the name lists.")

    lines.append("*Study aid only — not a full chart reading.*")
    return "\n\n".join(lines)


PADA_NOTE = {
    1: "Pada **1** (Aries sub-tone) stresses initiative and a fresh stake in this star’s agenda.",
    2: "Pada **2** (Taurus sub-tone) grounds the theme in stability, value, and what can be sustained.",
    3: "Pada **3** (Gemini sub-tone) turns the theme toward skill, dialogue, networks, and adaptation.",
    4: "Pada **4** (Cancer sub-tone) deepens feeling, protection, closure, or a more private side of the star.",
}

NAK_CORE = {
    "Ashwini": (
        "Ashwini is the doctor-horse constellation: quick starts, rescue, and the courage to enter the unknown. "
        "There is innocence mixed with competence — healing often arrives through motion, not waiting."
    ),
    "Bharani": (
        "Bharani holds the womb of transformation: what must be carried, endured, and delivered with integrity. "
        "Desire and duty meet here; ethical restraint turns intensity into creative power."
    ),
    "Krittika": (
        "Krittika is the razor-flame: discernment, purification, and cutting through excuses. "
        "Truth-telling and focus matter; anger managed becomes protective clarity."
    ),
    "Rohini": (
        "Rohini is the fertile field: growth, beauty, magnetism, and the art of cultivation. "
        "What you tend steadily tends to flourish; attachment to comfort is the shadow to watch."
    ),
    "Mrigashira": (
        "Mrigashira is the searching deer: curiosity, gentleness, and the chase for meaning or love. "
        "Restlessness resolves when the quest aims at something worthy rather than endless novelty."
    ),
    "Ardra": (
        "Ardra is the storm that clears: emotional weather, sharp insight after upheaval. "
        "Catharsis and honesty are medicines; the mind learns to serve the heart."
    ),
    "Punarvasu": (
        "Punarvasu is the return of light: renewal after loss, teaching, and simple shelter. "
        "Hope is practical here — generosity and patience rebuild what broke."
    ),
    "Pushya": (
        "Pushya is the nourisher’s star: ethics, care, and the slow strength of the good shepherd. "
        "Protection and service elevate status; rigid “shoulds” are the trap."
    ),
    "Ashlesha": (
        "Ashlesha is the coiled serpent: persuasion, psychology, and intensity around attachment. "
        "Words and insight are powerful; transparency keeps intimacy clean."
    ),
    "Magha": (
        "Magha is the throne-room of ancestors: dignity, ceremony, and the weight of lineage. "
        "Authority is earned through respect for those who came before — and humility before power."
    ),
    "Purva Phalguni": (
        "Purva Phalguni is the hammock of creative ease: union, rest, celebration, and fertile joy. "
        "Love and art need leisure to bloom; over-indulgence dulls the gift."
    ),
    "Uttara Phalguni": (
        "Uttara Phalguni is the marriage of patronage: contracts, loyalty, and lasting bonds. "
        "Promises kept in public build real security; pride can strain partnership."
    ),
    "Hasta": (
        "Hasta is the clever hand: craft, wit, service, and tangible skill. "
        "Small honest work compounds; sarcasm or trickery wastes the dexterity."
    ),
    "Chitra": (
        "Chitra is the bright jewel: design, one shining peak, and the wish to be seen as excellent. "
        "Beauty and architecture matter; vanity is the shadow when the form forgets the soul."
    ),
    "Swati": (
        "Swati is the independent wind: trade, autonomy, and movement on one’s own terms. "
        "Flexibility is strength; scattered commitments dilute the breeze."
    ),
    "Vishakha": (
        "Vishakha is the forked goal: obsession with a single target, transformation through ambition. "
        "Victory tastes better when ethics stay in the chariot."
    ),
    "Anuradha": (
        "Anuradha is devotion in friendship: teamwork, loyalty, success after steady effort. "
        "Belonging heals; clinging or suspicion corrodes the alliance."
    ),
    "Jyeshtha": (
        "Jyeshtha is the elder’s umbrella: protection, intensity, and responsibility for the circle. "
        "Maturity shows as calm authority; control masked as care is the pitfall."
    ),
    "Mula": (
        "Mula is the root and uprooting: investigation, truth at the foundation, sometimes chaos before clarity. "
        "Courage to dismantle false stories clears space for dharma."
    ),
    "Purva Ashadha": (
        "Purva Ashadha is the undefeated wave: declaration, charisma, and emotional courage. "
        "Inspiration moves people; pride in the mask can distance the heart."
    ),
    "Uttara Ashadha": (
        "Uttara Ashadha is victory in time: patience, dharma, and the slow crown of persistence. "
        "The last steps matter most; rigidity can miss mercy."
    ),
    "Shravana": (
        "Shravana is the listening ear: tradition, connection, and learning through careful attention. "
        "Reputation grows when speech aligns with what was actually heard."
    ),
    "Dhanishta": (
        "Dhanishta is the drum of rhythm: music, timing, and visibility in community. "
        "Wealth of fame or fellowship follows coherent beats; scattered noise wastes the talent."
    ),
    "Shatabhisha": (
        "Shatabhisha is the hundred healers: mystery, systems medicine, and truth behind the veil. "
        "Solitude and study deepen power; isolation without service turns cold."
    ),
    "Purva Bhadrapada": (
        "Purva Bhadrapada is the front of the funeral cot: passion, tapas, and depth that borders the sacred. "
        "Intensity consecrated becomes transformation; unchecked it burns the holder."
    ),
    "Uttara Bhadrapada": (
        "Uttara Bhadrapada is the serpent of the deep lake: wisdom, steadiness, and spiritual sleep that heals. "
        "Calm leadership serves many; withdrawal can become avoidance if fear runs the show."
    ),
    "Revati": (
        "Revati is the journey’s end that begins again: protection, closure, and safe passage. "
        "Compassion and guidance finish cycles well; worry for every stray detail exhausts the shepherd."
    ),
}


def _nak_block(body: BodyPos) -> str:
    core = NAK_CORE.get(
        body.nakshatra,
        "Study this nakshatra’s deity, myth, and shakti in your lineage — pada refines *how* the theme acts out.",
    )
    pada = PADA_NOTE.get(body.pada, f"Pada **{body.pada}** modulates how finely this star’s theme expresses.")
    return (
        f"##### {body.name} — **{body.nakshatra}**, pada **{body.pada}** "
        f"(D1 **{body.sign_d1}**)\n{core} {pada}"
    )


def nakshatra_picture_markdown(bodies: list) -> str:
    """Narrative summary of nakshatra placements (Lagna & luminaries first)."""
    order = ["Lagna", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    by_name = {b.name: b for b in bodies}
    blocks = [
        "**Nakshatras** — Moon = inner climate; Lagna = how you step forward; other grahas tint what that planet means. "
        "Pada is which quarter of the star (1–4), not a new star."
    ]
    for nm in order:
        b = by_name.get(nm)
        if b:
            blocks.append(_nak_block(b))
    return "\n\n".join(blocks)


def nakshatra_blurb(name: str, nak: str, pada: int) -> str:
    """Legacy one-liner (kept for tests or external use)."""
    core = NAK_CORE.get(nak, "Study this nakshatra in your tradition.")
    p = PADA_NOTE.get(pada, f"Pada {pada} refines expression.")
    return f"**{name}** in **{nak}** pada **{pada}** — {core} {p}"
