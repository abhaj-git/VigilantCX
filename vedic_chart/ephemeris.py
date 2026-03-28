from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import swisseph as swe

from . import varga

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL


def ayanamsa_choices() -> list[tuple[str, int]]:
    """Labels and Swiss Ephemeris sidereal mode constants."""
    return [
        ("Lahiri (Chitrapaksha)", swe.SIDM_LAHIRI),
        ("Raman", swe.SIDM_RAMAN),
        ("Krishnamurti (KP)", swe.SIDM_KRISHNAMURTI),
    ]


@dataclass
class BodyPos:
    name: str
    lon: float
    sign_d1: str
    vargas: dict[int, str]
    nakshatra: str
    pada: int


def _jd_ut(dt_utc: datetime) -> float:
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
        + dt_utc.microsecond / 3.6e9
    )
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def compute_chart(
    dt_utc: datetime,
    lat: float,
    lon: float,
    *,
    sid_mode: int | None = None,
) -> list[BodyPos]:
    """
    Sidereal positions (ayanamsa set via sid_mode, default Lahiri).
    dt_utc must be timezone-aware UTC. Returns bodies with Lagna first, then Grahas.
    """
    swe.set_sid_mode(sid_mode if sid_mode is not None else swe.SIDM_LAHIRI)
    jd = _jd_ut(dt_utc)

    bodies_spec = [
        ("Sun", swe.SUN),
        ("Moon", swe.MOON),
        ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS),
        ("Saturn", swe.SATURN),
        ("Rahu", swe.MEAN_NODE),
    ]

    out: list[BodyPos] = []

    from .nakshatra import nakshatra_pada

    for name, pid in bodies_spec:
        xx, _ = swe.calc_ut(jd, pid, FLAGS)
        plon = xx[0] % 360.0
        s1 = varga.varga_sign(plon, 1)
        vmap = {d: SIGNS[varga.varga_sign(plon, d)] for d in range(1, 11)}
        nak, pada, _ = nakshatra_pada(plon)
        out.append(
            BodyPos(
                name=name,
                lon=plon,
                sign_d1=SIGNS[s1],
                vargas=vmap,
                nakshatra=nak,
                pada=pada,
            )
        )

    ketu_lon = (out[-1].lon + 180.0) % 360.0
    s1k = varga.varga_sign(ketu_lon, 1)
    vmap_k = {d: SIGNS[varga.varga_sign(ketu_lon, d)] for d in range(1, 11)}
    nak_k, pada_k, _ = nakshatra_pada(ketu_lon)
    out.append(
        BodyPos(
            name="Ketu",
            lon=ketu_lon,
            sign_d1=SIGNS[s1k],
            vargas=vmap_k,
            nakshatra=nak_k,
            pada=pada_k,
        )
    )

    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    asc_tropical = ascmc[0] % 360.0
    ayan = swe.get_ayanamsa_ut(jd)
    asc_sid = swe.degnorm(asc_tropical - ayan) % 360.0

    nak_l, pada_l, _ = nakshatra_pada(asc_sid)
    s1l = varga.varga_sign(asc_sid, 1)
    vmap_l = {d: SIGNS[varga.varga_sign(asc_sid, d)] for d in range(1, 11)}
    lagna = BodyPos(
        name="Lagna",
        lon=asc_sid,
        sign_d1=SIGNS[s1l],
        vargas=vmap_l,
        nakshatra=nak_l,
        pada=pada_l,
    )
    return [lagna] + out
