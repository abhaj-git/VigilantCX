"""
Streamlit UI: birth data → D1 vs D9 / D1 vs D10, then summary + assessment.
Run from repo root:  streamlit run vedic_chart/app.py
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from vedic_chart.ephemeris import ayanamsa_choices, compute_chart
from vedic_chart.interpret import (
    chart_assessment_markdown,
    chart_summary_markdown,
    compare_d1_dn,
    layer_comparison_narrative,
    nakshatra_picture_markdown,
)

st.set_page_config(
    page_title="Vedic chart workbench",
    page_icon="☉",
    layout="wide",
)

st.title("Vedic chart workbench")
st.caption(
    "Swiss Ephemeris · Parashari-style D1–D10 (verify critical charts in JHora). "
    "Pick the **same ayanamsa** as the software you compare to. Educational templates only."
)


def _to_24h(hour_12: int, minute: int, am_pm: str) -> tuple[int, int]:
    if am_pm == "AM":
        h24 = 0 if hour_12 == 12 else hour_12
    else:
        h24 = 12 if hour_12 == 12 else hour_12 + 12
    return h24, minute


@st.cache_data(ttl=86400)
def resolve_place(place: str) -> tuple[float, float, str]:
    geo = Nominatim(user_agent="vedic_chart_workbench/1.0 (local)")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError("Could not geocode that place. Try city, state, country spelled out.")
    lat, lon = float(loc.latitude), float(loc.longitude)
    tzname = TimezoneFinder().timezone_at(lng=lon, lat=lat)
    if not tzname:
        raise ValueError("Could not resolve timezone for coordinates.")
    return lat, lon, tzname


_ayan_labels = [a[0] for a in ayanamsa_choices()]
_ayan_modes = [a[1] for a in ayanamsa_choices()]
_today = date.today()
_default_dob = date(1990, 1, 15)
if _default_dob > _today:
    _default_dob = _today

with st.sidebar:
    st.header("Birth data")
    city = st.text_input("City / town", placeholder="e.g. Mumbai")
    state = st.text_input("State / region", placeholder="e.g. Maharashtra")
    country = st.text_input("Country", placeholder="e.g. India")
    ayan_ix = st.selectbox("Ayanamsa", options=range(len(_ayan_labels)), format_func=lambda i: _ayan_labels[i], index=0)
    birth_date = st.date_input(
        "Date of birth",
        value=_default_dob,
        min_value=date(1800, 1, 1),
        max_value=_today,
    )
    st.markdown("**Time of birth (local)**")
    c1, c2, c3 = st.columns(3)
    with c1:
        hour_12 = st.selectbox("Hour", options=list(range(1, 13)), index=11, format_func=lambda h: f"{h:02d}")
    with c2:
        minute = st.selectbox("Minute", options=list(range(0, 60)), format_func=lambda m: f"{m:02d}")
    with c3:
        am_pm = st.selectbox("AM / PM", options=["AM", "PM"], index=0)

    manual_tz = st.text_input(
        "Override timezone (IANA, optional)",
        placeholder="e.g. Asia/Kolkata",
        help="If geocoding fails or historic TZ is wrong, set e.g. Asia/Kolkata",
    )
    run = st.button("Calculate", type="primary")

if run:
    if not city.strip() or not country.strip():
        st.error("Enter at least **city** and **country**.")
        st.stop()
    parts = [city.strip()]
    if state.strip():
        parts.append(state.strip())
    parts.append(country.strip())
    place_query = ", ".join(parts)

    try:
        if manual_tz.strip():
            lat, lon, tzname = resolve_place(place_query)
            tzname = manual_tz.strip()
            try:
                ZoneInfo(tzname)
            except Exception:
                st.error("Invalid IANA timezone string.")
                st.stop()
        else:
            lat, lon, tzname = resolve_place(place_query)
    except Exception as e:
        st.error(str(e))
        st.stop()

    h24, mi = _to_24h(hour_12, minute, am_pm)
    local_dt = datetime(
        birth_date.year,
        birth_date.month,
        birth_date.day,
        h24,
        mi,
        tzinfo=ZoneInfo(tzname),
    )
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    sid_mode = _ayan_modes[ayan_ix]
    ayan_label = _ayan_labels[ayan_ix]

    try:
        bodies = compute_chart(utc_dt, lat, lon, sid_mode=sid_mode)
    except Exception as e:
        st.error(f"Ephemeris error: {e}")
        st.stop()

    st.markdown(
        f"**Resolved:** {place_query} → {lat:.4f}°, {lon:.4f}° · **{tzname}** · **{ayan_label}** · "
        f"Local **{local_dt:%Y-%m-%d %I:%M %p}** · UTC **{utc_dt:%Y-%m-%d %H:%M}**"
    )
    st.caption(
        "D9 = navamsa (inner / partnership tone). D10 = dasamsa (work & how you’re seen). "
        "Each row below says only what’s different for that graha — no repeated boilerplate."
    )

    with st.expander("Technical — sidereal longitude & D1/D9 (for cross-check)"):
        st.caption("Compare these longitudes and signs with your reference app using the **same ayanamsa** and **exact birth local time**.")
        for name in ("Lagna", "Moon", "Sun", "Saturn"):
            b = next((x for x in bodies if x.name == name), None)
            if b:
                st.markdown(
                    f"**{b.name}** · λ {b.lon:.5f}° · D1 **{b.sign_d1}** · D9 **{b.vargas[9]}** · "
                    f"nakshatra **{b.nakshatra}** pada **{b.pada}**"
                )

    st.subheader("D1 vs D9 — per point")
    for b in bodies:
        line, blurb = compare_d1_dn(b, 9)
        st.markdown(f"- {line}")
        st.caption(blurb)

    st.subheader("D9 — who lines up")
    st.markdown(layer_comparison_narrative(bodies, 9))

    st.subheader("D1 vs D10 — per point")
    for b in bodies:
        line, blurb = compare_d1_dn(b, 10)
        st.markdown(f"- {line}")
        st.caption(blurb)

    st.subheader("D10 — who lines up")
    st.markdown(layer_comparison_narrative(bodies, 10))

    st.subheader("Nakshatra summaries")
    st.markdown(nakshatra_picture_markdown(bodies))

    st.subheader("Summary")
    st.markdown(chart_summary_markdown(bodies))

    st.subheader("Assessment")
    st.markdown(chart_assessment_markdown(bodies))

else:
    st.info("Enter birth location, date, and time (AM/PM), then click **Calculate**.")
