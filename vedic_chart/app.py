"""
Streamlit UI: birth data → D1 vs D9 / D1 vs D10, then summary + assessment.
Run from repo root:  streamlit run vedic_chart/app.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geopy.exc import GeocoderRateLimited, GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from vedic_chart.ephemeris import ayanamsa_choices, compute_chart
from vedic_chart.interpret import (
    chart_assessment_markdown,
    chart_summary_markdown,
    layer_comparison_narrative,
    nakshatra_picture_markdown,
)
from vedic_chart.varga_narratives import varga_detail_block, varga_detail_intro

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


_UA = "vedic_chart_workbench/1.0 (contact: local-use; respects nominatim usage policy)"


def _photon_lat_lon(query: str) -> tuple[float, float] | None:
    """Fallback geocoder (no API key). Used when OpenStreetMap Nominatim returns 429."""
    q = urllib.parse.quote(query.strip())
    url = f"https://photon.komoot.io/api/?q={q}&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None
        raise
    feats = data.get("features") or []
    if not feats:
        return None
    coords = feats[0]["geometry"]["coordinates"]
    lon, lat = float(coords[0]), float(coords[1])
    return lat, lon


def resolve_place(place: str) -> tuple[float, float, str]:
    """
    Lat/lon + IANA timezone from place name.
    Retries Nominatim on 429; falls back to Photon if needed.
    Not Streamlit-cached so 429 isn’t stuck after a bad run.
    """
    geo = Nominatim(user_agent=_UA)
    loc = None
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            loc = geo.geocode(place, timeout=25)
            break
        except GeocoderRateLimited as e:
            last_err = e
            time.sleep(min(8.0, 1.5 ** attempt))
        except GeocoderTimedOut as e:
            last_err = e
            time.sleep(1.0 + attempt)
        except GeocoderServiceError as e:
            last_err = e
            msg = str(e).lower()
            if "429" in msg or "too many" in msg:
                time.sleep(min(8.0, 1.5 ** attempt))
            else:
                raise
    lat: float | None = None
    lon: float | None = None
    if loc is not None:
        lat, lon = float(loc.latitude), float(loc.longitude)
    else:
        pair = _photon_lat_lon(place)
        if pair is None:
            hint = (
                " OpenStreetMap (Nominatim) rate-limited this request (HTTP 429). "
                "Fill **Latitude**, **Longitude**, and **Timezone** in the sidebar, or wait a minute and try again."
            )
            raise ValueError(
                (str(last_err) if last_err else "Geocoding failed.") + hint
            )
        lat, lon = pair

    tzname = TimezoneFinder().timezone_at(lng=lon, lat=lat)
    if not tzname:
        raise ValueError("Could not resolve timezone for coordinates — set **Override timezone** manually.")
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
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat_in = st.text_input(
            "Latitude °",
            placeholder="optional",
            help="Decimal degrees. N = positive, S = negative. Leave blank to use city lookup.",
        )
    with col_lon:
        lon_in = st.text_input(
            "Longitude °",
            placeholder="optional",
            help="Decimal degrees. E = positive, W = negative.",
        )
    st.caption("If **both** lat and long are filled, city lookup is skipped (good for 429 errors). You must set **Timezone**.")
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

    tz_in = st.text_input(
        "Timezone (IANA)",
        placeholder="e.g. Asia/Kolkata",
        help="Required if you enter lat/long. Optional: overrides timezone after city lookup.",
    )
    run = st.button("Calculate", type="primary")

if run:
    lat_s = lat_in.strip() if lat_in else ""
    lon_s = lon_in.strip() if lon_in else ""

    if lat_s and lon_s:
        try:
            lat = float(lat_s)
            lon = float(lon_s)
        except ValueError:
            st.error("Latitude and longitude must be decimal numbers (e.g. `19.076` and `72.878`).")
            st.stop()
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            st.error("Latitude must be −90…90 and longitude −180…180.")
            st.stop()
        if not tz_in.strip():
            st.error("Enter **Timezone (IANA)** when using latitude and longitude (e.g. `Asia/Kolkata`).")
            st.stop()
        try:
            ZoneInfo(tz_in.strip())
        except Exception:
            st.error("Invalid timezone. Use an IANA name like `Asia/Kolkata` or `America/New_York`.")
            st.stop()
        tzname = tz_in.strip()
        place_query = f"{lat:.5f}°, {lon:.5f}°"
    elif lat_s or lon_s:
        st.error("Enter **both** latitude and longitude, or leave both blank to use city lookup.")
        st.stop()
    else:
        if not city.strip() or not country.strip():
            st.error("Enter **city** and **country**, or fill **latitude** and **longitude**.")
            st.stop()
        parts = [city.strip()]
        if state.strip():
            parts.append(state.strip())
        parts.append(country.strip())
        place_query = ", ".join(parts)

        try:
            lat, lon, tzname = resolve_place(place_query)
            if tz_in.strip():
                try:
                    ZoneInfo(tz_in.strip())
                except Exception:
                    st.error("Invalid IANA timezone string.")
                    st.stop()
                tzname = tz_in.strip()
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
    st.caption("Below: detailed **D1→D9** and **D1→D10** lines for each point (like a short note per graha).")

    with st.expander("Technical — sidereal longitude & D1/D9 (for cross-check)"):
        st.caption("Compare these longitudes and signs with your reference app using the **same ayanamsa** and **exact birth local time**.")
        for name in ("Lagna", "Moon", "Sun", "Saturn"):
            b = next((x for x in bodies if x.name == name), None)
            if b:
                st.markdown(
                    f"**{b.name}** · λ {b.lon:.5f}° · D1 **{b.sign_d1}** · D9 **{b.vargas[9]}** · "
                    f"nakshatra **{b.nakshatra}** pada **{b.pada}**"
                )

    st.subheader("D1 → D9 (navamsa)")
    st.markdown(varga_detail_intro(9))
    for i, b in enumerate(bodies):
        st.markdown(varga_detail_block(b, 9))
        if i < len(bodies) - 1:
            st.divider()

    st.subheader("D9 — who lines up")
    st.markdown(layer_comparison_narrative(bodies, 9))

    st.subheader("D1 → D10 (dasamsa)")
    st.markdown(varga_detail_intro(10))
    for i, b in enumerate(bodies):
        st.markdown(varga_detail_block(b, 10))
        if i < len(bodies) - 1:
            st.divider()

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
