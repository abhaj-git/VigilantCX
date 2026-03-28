"""
Streamlit UI: birth data → D1–D10 signs, D1 vs D9 / D1 vs D10 summaries, nakshatra/pada.
Run from repo root:  streamlit run vedic_chart/app.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from vedic_chart.ephemeris import compute_chart
from vedic_chart.interpret import compare_d1_dn, nakshatra_blurb

st.set_page_config(
    page_title="Vedic chart workbench",
    page_icon="☉",
    layout="wide",
)

st.title("Vedic chart workbench")
st.caption(
    "Lahiri sidereal · Swiss Ephemeris · Parashari-style D1–D10 (verify critical charts in JHora). "
    "Educational templates — not medical, legal, or financial advice."
)


@st.cache_data(ttl=86400)
def resolve_place(place: str) -> tuple[float, float, str]:
    geo = Nominatim(user_agent="vedic_chart_workbench/1.0 (local)")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError("Could not geocode that place. Try city, region, country.")
    lat, lon = float(loc.latitude), float(loc.longitude)
    tzname = TimezoneFinder().timezone_at(lng=lon, lat=lat)
    if not tzname:
        raise ValueError("Could not resolve timezone for coordinates.")
    return lat, lon, tzname


with st.sidebar:
    st.header("Birth data")
    place = st.text_input("Place of birth", placeholder="e.g. Mumbai, India")
    birth_date = st.date_input("Date of birth")
    birth_time = st.time_input("Time of birth (local to place)")
    manual_tz = st.text_input(
        "Override timezone (IANA, optional)",
        placeholder="e.g. Asia/Kolkata",
        help="If geocoding fails or historic TZ is wrong, set e.g. Asia/Kolkata",
    )
    run = st.button("Calculate", type="primary")

if run:
    if not place.strip():
        st.error("Enter a birth place.")
        st.stop()
    try:
        if manual_tz.strip():
            lat, lon, tzname = resolve_place(place.strip())
            tzname = manual_tz.strip()
            try:
                ZoneInfo(tzname)
            except Exception:
                st.error("Invalid IANA timezone string.")
                st.stop()
        else:
            lat, lon, tzname = resolve_place(place.strip())
    except Exception as e:
        st.error(str(e))
        st.stop()

    local_dt = datetime(
        birth_date.year,
        birth_date.month,
        birth_date.day,
        birth_time.hour,
        birth_time.minute,
        tzinfo=ZoneInfo(tzname),
    )
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    try:
        bodies = compute_chart(utc_dt, lat, lon)
    except Exception as e:
        st.error(f"Ephemeris error: {e}")
        st.stop()

    st.success(f"Resolved **{place.strip()}** → {lat:.4f}°, {lon:.4f}° · **{tzname}** · UTC **{utc_dt:%Y-%m-%d %H:%M}**")

    st.subheader("D1 vs D9 — per point")
    for b in bodies:
        line, blurb = compare_d1_dn(b, 9)
        st.markdown(f"- {line}")
        st.caption(blurb)

    st.subheader("D1 vs D10 — per point")
    for b in bodies:
        line, blurb = compare_d1_dn(b, 10)
        st.markdown(f"- {line}")
        st.caption(blurb)

    st.subheader("Planets, Lagna — signs D1–D10 · nakshatra · pada")
    rows = []
    for b in bodies:
        rows.append(
            {
                "Point": b.name,
                "D1": b.sign_d1,
                "D2": b.vargas[2],
                "D3": b.vargas[3],
                "D4": b.vargas[4],
                "D5": b.vargas[5],
                "D6": b.vargas[6],
                "D7": b.vargas[7],
                "D8": b.vargas[8],
                "D9": b.vargas[9],
                "D10": b.vargas[10],
                "Nakshatra": b.nakshatra,
                "Pada": b.pada,
                "Lon°": round(b.lon, 4),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Nakshatra / pada — short notes")
    for b in bodies:
        st.markdown(nakshatra_blurb(b.name, b.nakshatra, b.pada))

else:
    st.info("Enter birth place, date, and local time, then click **Calculate**.")
