"""World-anchored hex grid math (v0.2, design doc §6).

Maps cube coordinates to real-world positions using the EXACT same constants
and formulas as the web frontend (``src/frontend/src/utils/hexUtils.ts``) so
printed tiles correspond 1:1 to the map grid:

- Origin (0,0,0) = Haden, Norway (lat 61.238408, lon 7.712059).
- Pointy-top hexes, center-to-center spacing 4828.032 m (3 miles).
- Local equirectangular meter space (NOT Web-Mercator): meters per degree of
  longitude scaled by cos(origin latitude).

This module is bpy-free and unit-tested with plain Python.
"""

from __future__ import annotations

import math

from .coordinates import CubeCoord

# --- Constants (must match src/frontend/src/utils/hexUtils.ts) ---------------

#: Origin latitude (Haden, Norway).
ORIGIN_LAT: float = 61.238408
#: Origin longitude (Haden, Norway).
ORIGIN_LNG: float = 7.712059
#: Center-to-center distance in meters (3 miles).
HEX_CENTER_SPACING_M: float = 4828.032
#: Hex circumradius / edge length in meters: center_spacing / sqrt(3).
HEX_SIZE_M: float = HEX_CENTER_SPACING_M / math.sqrt(3.0)
#: Meters per degree of latitude (approximately constant).
METERS_PER_DEGREE_LAT: float = 111320.0
#: Meters per degree of longitude at the origin latitude.
METERS_PER_DEGREE_LNG: float = METERS_PER_DEGREE_LAT * math.cos(
    math.radians(ORIGIN_LAT)
)

_SQRT3: float = math.sqrt(3.0)


def hex_to_meters(coord: CubeCoord) -> tuple[float, float]:
    """Hex center offset from the origin in meters (pointy-top).

    Mirrors ``hexToPixel``: ``x = size*sqrt(3)*(q + r/2)``,
    ``y = size*1.5*r``.
    """
    q: float = float(coord.q)
    r: float = float(coord.r)
    x: float = HEX_SIZE_M * _SQRT3 * (q + r / 2.0)
    y: float = HEX_SIZE_M * 1.5 * r
    return x, y


def meters_to_latlng(point: tuple[float, float]) -> tuple[float, float]:
    """Meters relative to the origin -> (lat, lng).

    Mirrors ``metersToLatLng`` (local equirectangular projection).
    """
    x: float = point[0]
    y: float = point[1]
    lat: float = ORIGIN_LAT + y / METERS_PER_DEGREE_LAT
    lng: float = ORIGIN_LNG + x / METERS_PER_DEGREE_LNG
    return lat, lng


def latlng_to_meters(lat: float, lng: float) -> tuple[float, float]:
    """(lat, lng) -> meters relative to the origin.

    Mirrors ``latLngToMeters`` (inverse of :func:`meters_to_latlng`).
    """
    x: float = (lng - ORIGIN_LNG) * METERS_PER_DEGREE_LNG
    y: float = (lat - ORIGIN_LAT) * METERS_PER_DEGREE_LAT
    return x, y


def hex_to_latlng(coord: CubeCoord) -> tuple[float, float]:
    """Hex center -> (lat, lng). Mirrors ``hexToLatLng``."""
    return meters_to_latlng(hex_to_meters(coord))


def _hex_round(q_frac: float, r_frac: float) -> CubeCoord:
    """Round fractional axial coords to the nearest valid cube coord.

    Mirrors ``pixelToHex`` + ``hexRound``: the component with the largest
    rounding error is reset to satisfy ``q + r + s == 0``.
    """
    s_frac: float = -q_frac - r_frac
    q: int = round(q_frac)
    r: int = round(r_frac)
    s: int = round(s_frac)
    q_diff: float = abs(q - q_frac)
    r_diff: float = abs(r - r_frac)
    s_diff: float = abs(s - s_frac)
    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    else:
        s = -q - r
    return CubeCoord(q, r, s)


def latlng_to_hex(lat: float, lng: float) -> CubeCoord:
    """(lat, lng) -> nearest hex coordinate. Mirrors ``latLngToHex``."""
    x: float
    y: float
    x, y = latlng_to_meters(lat, lng)
    q_frac: float = (_SQRT3 / 3.0 * x - 1.0 / 3.0 * y) / HEX_SIZE_M
    r_frac: float = (2.0 / 3.0 * y) / HEX_SIZE_M
    return _hex_round(q_frac, r_frac)


def hex_footprint_meters(coord: CubeCoord) -> list[tuple[float, float]]:
    """The 6 corner points of a hex in meters (pointy-top).

    Mirrors ``getHexCorners``: corner *i* is at angle ``30 + 60*i`` degrees,
    radius :data:`HEX_SIZE_M`, around the hex center.
    """
    cx: float
    cy: float
    cx, cy = hex_to_meters(coord)
    corners: list[tuple[float, float]] = []
    for i in range(6):
        ang: float = math.radians(30.0 + 60.0 * i)
        corners.append(
            (cx + HEX_SIZE_M * math.cos(ang), cy + HEX_SIZE_M * math.sin(ang))
        )
    return corners
