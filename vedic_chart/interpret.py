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


_GRAHA_D9_ROLE = {
    "Lagna": "the body, temperament, and how life *approaches* you",
    "Sun": "core identity, father-figures, vitality, and dharma-direction",
    "Moon": "mind, mother-nourishment, emotional habit, and what feels like “home”",
    "Mars": "courage, siblings, conflict style, and where you push",
    "Mercury": "speech, learning, commerce, and clever adaptation",
    "Jupiter": "guidance, children, faith, and what expands you",
    "Venus": "relationships, arts, comfort, and what you draw toward you",
    "Saturn": "duty, time-tests, structure, and where life asks patience",
    "Rahu": "hunger, obsession, foreign or unusual threads",
    "Ketu": "release, intuition, and what you’ve already metabolized",
}

_GRAHA_D10_ROLE = {
    "Lagna": "public mask and how you’re met in professional settings",
    "Sun": "authority, recognition, and leadership in the world",
    "Moon": "public mood, reputation for care, and workplace needs",
    "Mars": "competition, technical fight, and drive on the job",
    "Mercury": "analysis, messaging, deals, and skill-based work",
    "Jupiter": "teaching, advising, ethics visible in career",
    "Venus": "alliances, design, client harmony, and reward through people",
    "Saturn": "long arcs, seniority, systems, and earned status",
    "Rahu": "ambition, niche expertise, or unconventional career edges",
    "Ketu": "detachment from titles, research, or behind-the-scenes mastery",
}


def _blurb(body: BodyPos, rel: str, d_high: int) -> str:
    chart = "navamsa (D9)" if d_high == 9 else "dasamsa (D10)"
    role = (
        _GRAHA_D9_ROLE.get(body.name, "this point’s life themes")
        if d_high == 9
        else _GRAHA_D10_ROLE.get(body.name, "this point’s life themes")
    )
    head = ""
    if rel == "same":
        head = (
            f"D1 and {chart} share the **same sign** — what shows at the rashi level and what refines in "
            f"{chart} move together for **{body.name}** ({role}). The story is easier to read as one thread."
        )
    elif rel == "trine":
        head = (
            f"D1 and {chart} connect by **trine** — supportive, same-element resonance for **{body.name}** "
            f"({role}). Outer life and the {chart} layer help each other without identical signs."
        )
    elif rel == "opposition":
        head = (
            f"D1 and {chart} **oppose** — a see-saw for **{body.name}** ({role}): the world sees one emphasis "
            f"while {chart} matures through the opposite pole. Balance is the curriculum."
        )
    elif rel == "tension_6_8":
        head = (
            f"D1 and {chart} sit in a **6/8 (hidden-stress)** style link for **{body.name}** ({role}). "
            "One layer must serve or transform the other; friction often becomes skill over time."
        )
    elif rel == "square":
        head = (
            f"D1 and {chart} **square** for **{body.name}** ({role}) — productive tension, decisions, "
            f"and the need to act rather than drift. Channelled well, it builds competence."
        )
    else:
        head = (
            f"D1 and {chart} relate in a **mixed / neutral** way for **{body.name}** ({role}) — "
            "not a loud harmony or clash; house lords, dignity, and transits finish the story."
        )

    tail = (
        " In classical usage D9 refines marriage, subtle self, and *bhava* promise; weigh strength and aspects in a full chart."
        if d_high == 9
        else " D10 is read for career, office politics, and how effort becomes reputation — still only one slice of the whole map."
    )
    return head + tail


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
    """Counts plus a short cross-chart reading."""
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

    n = len(bodies)
    same9 = c9.get("same", 0)
    same10 = c10.get("same", 0)
    easy9 = same9 + c9.get("trine", 0)
    easy10 = same10 + c10.get("trine", 0)
    hard9 = c9.get("tension_6_8", 0) + c9.get("square", 0)
    hard10 = c10.get("tension_6_8", 0) + c10.get("square", 0)

    story = []
    if easy9 >= n * 0.55:
        story.append(
            "**Overall D9:** Many easy agreements (same or trine) between rashi and navamsa — inner and outer "
            "versions of the grahas tend to rhyme; life themes may feel comparatively coherent."
        )
    elif hard9 >= n * 0.45:
        story.append(
            "**Overall D9:** Several sharp D1/D9 angles — inner refinement asks for honesty where the rashi story "
            "is simple; relationships and subtle expectations often carry the integration homework."
        )
    else:
        story.append(
            "**Overall D9:** A mixed signature — some grahas echo cleanly in navamsa, others ask for translation. "
            "Read the highlighted names in the list above as your personal “high attention” points."
        )

    if easy10 >= n * 0.55:
        story.append(
            "**Overall D10:** Strong trine/same flow into dasamsa — the way you work and are seen may follow "
            "naturally from the birth-chart story, once skills catch up to the promise."
        )
    elif hard10 >= n * 0.45:
        story.append(
            "**Overall D10:** Career and public life may not mirror the rashi chart line-for-line — effort, "
            "timing, and sometimes a second “public self” appear before reputation stabilizes."
        )
    else:
        story.append(
            "**Overall D10:** Moderate career overlay — neither fully mirrored nor fully opposed; promotion, "
            "role changes, and mentors tend to clarify which D10 lines matter most."
        )

    return (
        "**D9 layer (vs D1):** " + fmt(c9) + "\n\n"
        "**D10 layer (vs D1):** " + fmt(c10) + "\n\n"
        + "\n\n".join(story)
    )


def layer_comparison_narrative(bodies: list, n: int) -> str:
    """Meaning-rich paragraph after per-point D1 vs D9 or D1 vs D10."""
    assert n in (9, 10)
    name = "navamsa (D9)" if n == 9 else "dasamsa (D10)"
    focus = (
        "subtle self, partnership tone, and how promises in the rashi chart ripen inwardly"
        if n == 9
        else "work, duty cycles, recognition, and the story your résumé tells the world"
    )

    vargotta = [b.name for b in bodies if b.sign_d1 == b.vargas[n]]
    supportive = [
        b.name
        for b in bodies
        if _relation(b.sign_d1, b.vargas[n]) == "trine"
    ]
    stressed = [
        b.name
        for b in bodies
        if _relation(b.sign_d1, b.vargas[n]) in ("tension_6_8", "square")
    ]
    opposed = [b.name for b in bodies if _relation(b.sign_d1, b.vargas[n]) == "opposition"]

    chunks = [
        f"Taken together, this **{name}** picture describes **{focus}**. "
        "Same-sign pairs are often called *vargottama-style* echoes: the outer script and the divisional refinement "
        "speak the same language. Trines add help without identical signs; 6/8 and squares ask you to convert "
        "pressure into skill."
    ]
    if vargotta:
        chunks.append(
            "**Strongest resonance (D1 = D" + str(n) + "):** "
            + ", ".join(f"**{x}**" for x in vargotta)
            + " — these factors carry a double stamp; when you invest here, both layers respond."
        )
    if supportive:
        chunks.append(
            "**Supportive bridge:** " + ", ".join(f"**{x}**" for x in supportive) + "."
        )
    if opposed:
        chunks.append(
            "**Polarity to integrate:** " + ", ".join(f"**{x}**" for x in opposed) + " — negotiate both ends rather than picking one story."
        )
    if stressed:
        chunks.append(
            "**Growth-through-friction:** " + ", ".join(f"**{x}**" for x in stressed) + " — tension is information, not a verdict."
        )

    return "\n\n".join(chunks)


def chart_assessment_markdown(bodies: list) -> str:
    """Closing assessment (educational synthesis, not a full reading)."""
    c9 = _count_relations(bodies, 9)
    c10 = _count_relations(bodies, 10)
    n = len(bodies)
    same9 = c9.get("same", 0)
    same10 = c10.get("same", 0)
    tense9 = c9.get("tension_6_8", 0) + c9.get("square", 0)
    tense10 = c10.get("tension_6_8", 0) + c10.get("square", 0)

    lines = []
    lines.append(
        "**How to read this:** The per-point lines compare *rashi* (D1) with *navamsa* (D9) and *dasamsa* (D10). "
        "The combined paragraphs name where life feels coherent vs where it asks you to grow. "
        "**Nakshatra summaries** above spell out the emotional and mythic tone of each point."
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
        "**Nakshatra picture** — the Moon’s mansion colors mind and memory; Lagna’s mansion tints "
        "temperament; each graha lends its house’s “mood” to what that planet signifies. "
        "Pada quarters fine-tune *how* the star’s story moves — not a different star, but a different gear."
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
