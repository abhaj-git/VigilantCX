"""
Parashari-style divisional signs from sidereal ecliptic longitude (0–360°).
Widely used software conventions; cross-check critical charts with JHora / your guru.
"""
from __future__ import annotations


def _rashi(lon: float) -> int:
    return int(lon // 30) % 12


def _deg_in_sign(lon: float) -> float:
    return lon % 30.0


def _triplicity(r: int) -> int:
    """0 = movable (chara), 1 = fixed (sthira), 2 = dual (ubhaya)."""
    if r in (0, 3, 6, 9):
        return 0
    if r in (1, 4, 7, 10):
        return 1
    return 2


def _navamsa_start(r: int) -> int:
    """First navamsa (and panchamsa/shashthamsa) segment starts here."""
    t = _triplicity(r)
    if t == 0:
        return r
    if t == 1:
        return (r + 8) % 12
    return (r + 4) % 12


def _d7_start(r: int) -> int:
    t = _triplicity(r)
    if t == 0:
        return r
    if t == 1:
        return (r + 5) % 12
    return (r + 4) % 12


def _d8_start(r: int) -> int:
    t = _triplicity(r)
    if t == 0:
        return r
    if t == 1:
        return (r + 7) % 12
    return (r + 3) % 12


def varga_sign(lon: float, d: int) -> int:
    """Return zodiac sign index 0=Aries … 11=Pisces for division D1–D10."""
    lon = lon % 360.0
    if d == 1:
        return _rashi(lon)

    r = _rashi(lon)
    deg = _deg_in_sign(lon)

    if d == 2:
        h = int(deg // 15)
        if r % 2 == 0:
            return 4 if h == 0 else 3
        return 3 if h == 0 else 4

    if d == 3:
        part = min(2, int(deg // 10))
        return [r, (r + 4) % 12, (r + 8) % 12][part]

    if d == 4:
        part = min(3, int(deg // 7.5))
        return (r + [0, 3, 6, 9][part]) % 12

    if d == 5:
        part = min(4, int(deg // 6))
        return (_navamsa_start(r) + part) % 12

    if d == 6:
        part = min(5, int(deg // 5))
        return (_navamsa_start(r) + part) % 12

    if d == 7:
        part = min(6, int(deg // (30.0 / 7)))
        return (_d7_start(r) + part) % 12

    if d == 8:
        part = min(7, int(deg // (30.0 / 8)))
        return (_d8_start(r) + part) % 12

    if d == 9:
        part = min(8, int(deg * 9 // 30))
        if part > 8:
            part = 8
        return (_navamsa_start(r) + part) % 12

    if d == 10:
        part = min(9, int(deg // 3))
        start = r if (r % 2 == 0) else (r + 8) % 12
        return (start + part) % 12

    raise ValueError("Only D1–D10 supported")
