from __future__ import annotations

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

NAK_LEN = 360.0 / 27.0
PADA_LEN = NAK_LEN / 4.0


def nakshatra_pada(lon: float) -> tuple[str, int, float]:
    """Sidereal longitude → (nakshatra name, pada 1–4, longitude within nakshatra)."""
    lon = lon % 360.0
    idx = int(lon // NAK_LEN) % 27
    rem = lon - idx * NAK_LEN
    pada = int(rem // PADA_LEN) + 1
    if pada > 4:
        pada = 4
    return NAKSHATRAS[idx], pada, rem
