"""Border tests for the world-anchored hex grid (v0.2, design doc §6).

The add-on must map cube coordinates to real-world positions anchored at the
web map grid's origin (Haden, Norway) using the EXACT same math as
``src/frontend/src/utils/hexUtils.ts`` so printed tiles correspond 1:1 to the
map grid. These tests assert the public contract: origin location, neighbor
spacing, footprint corners, and the lat/lon <-> hex round trip.
"""

from __future__ import annotations

import math

from hex_heightmap_generator.coordinates import CubeCoord
from hex_heightmap_generator.worldgrid import (
    HEX_CENTER_SPACING_M,
    HEX_SIZE_M,
    METERS_PER_DEGREE_LAT,
    METERS_PER_DEGREE_LNG,
    ORIGIN_LAT,
    ORIGIN_LNG,
    hex_footprint_meters,
    hex_to_latlng,
    hex_to_meters,
    latlng_to_hex,
    meters_to_latlng,
)

TOL_M: float = 1e-6
TOL_DEG: float = 1e-9


def test_origin_hex_is_haden() -> None:
    lat, lng = hex_to_latlng(CubeCoord(0, 0, 0))
    assert abs(lat - 61.238408) < TOL_DEG
    assert abs(lng - 7.712059) < TOL_DEG
    assert abs(ORIGIN_LAT - 61.238408) < TOL_DEG
    assert abs(ORIGIN_LNG - 7.712059) < TOL_DEG


def test_constants_match_frontend() -> None:
    # hexUtils.ts: HEX_CENTER_SPACING_M = 4828.032 (3 miles),
    # HEX_SIZE_M = spacing / sqrt(3), METERS_PER_DEGREE_LAT = 111320.
    assert abs(HEX_CENTER_SPACING_M - 4828.032) < 1e-9
    assert abs(HEX_SIZE_M - 4828.032 / math.sqrt(3.0)) < 1e-9
    assert abs(METERS_PER_DEGREE_LAT - 111320.0) < 1e-9
    assert (
        abs(METERS_PER_DEGREE_LNG - 111320.0 * math.cos(math.radians(61.238408))) < 1e-9
    )


def test_hex_to_meters_matches_frontend_formula() -> None:
    # hexUtils.ts hexToPixel: x = size*sqrt(3)*(q + r/2), y = size*1.5*r.
    x, y = hex_to_meters(CubeCoord(1, 0, -1))
    assert abs(x - HEX_SIZE_M * math.sqrt(3.0)) < TOL_M
    assert abs(y - 0.0) < TOL_M
    x, y = hex_to_meters(CubeCoord(0, 1, -1))
    assert abs(x - HEX_SIZE_M * math.sqrt(3.0) * 0.5) < TOL_M
    assert abs(y - HEX_SIZE_M * 1.5) < TOL_M
    x, y = hex_to_meters(CubeCoord(0, 0, 0))
    assert abs(x) < TOL_M
    assert abs(y) < TOL_M


def test_adjacent_centers_are_three_miles_apart() -> None:
    # Every neighbor of the origin is exactly HEX_CENTER_SPACING_M away.
    origin: tuple[float, float] = hex_to_meters(CubeCoord(0, 0, 0))
    neighbors: list[CubeCoord] = [
        CubeCoord(1, 0, -1),
        CubeCoord(1, -1, 0),
        CubeCoord(0, -1, 1),
        CubeCoord(-1, 0, 1),
        CubeCoord(-1, 1, 0),
        CubeCoord(0, 1, -1),
    ]
    for n in neighbors:
        nx, ny = hex_to_meters(n)
        dist: float = math.hypot(nx - origin[0], ny - origin[1])
        assert abs(dist - HEX_CENTER_SPACING_M) < TOL_M, f"{n} -> {dist}"


def test_footprint_is_six_corners_at_hex_size() -> None:
    corners: list[tuple[float, float]] = hex_footprint_meters(CubeCoord(0, 0, 0))
    assert len(corners) == 6
    for i, (cx, cy) in enumerate(corners):
        # Pointy-top: corner i at angle 30 + 60*i degrees, radius HEX_SIZE_M.
        ang: float = math.radians(30.0 + 60.0 * i)
        assert abs(cx - HEX_SIZE_M * math.cos(ang)) < TOL_M
        assert abs(cy - HEX_SIZE_M * math.sin(ang)) < TOL_M


def test_footprint_follows_hex_center() -> None:
    # The footprint of a non-origin hex is the origin footprint translated by
    # the hex center offset.
    center: tuple[float, float] = hex_to_meters(CubeCoord(2, -1, -1))
    origin_corners: list[tuple[float, float]] = hex_footprint_meters(CubeCoord(0, 0, 0))
    moved: list[tuple[float, float]] = hex_footprint_meters(CubeCoord(2, -1, -1))
    for (ox, oy), (mx, my) in zip(origin_corners, moved):
        assert abs(mx - (ox + center[0])) < TOL_M
        assert abs(my - (oy + center[1])) < TOL_M


def test_meters_latlng_round_trip() -> None:
    lat, lng = meters_to_latlng((1234.5, -678.9))
    x, y = (
        (lng - ORIGIN_LNG) * METERS_PER_DEGREE_LNG,
        (lat - ORIGIN_LAT) * METERS_PER_DEGREE_LAT,
    )
    assert abs(x - 1234.5) < TOL_M
    assert abs(y - -678.9) < TOL_M


def test_latlng_to_hex_round_trip() -> None:
    # A hex center must round-trip back to the same hex.
    for coord in (
        CubeCoord(0, 0, 0),
        CubeCoord(1, 0, -1),
        CubeCoord(-3, 2, 1),
        CubeCoord(5, -5, 0),
        CubeCoord(-1, -1, 2),
    ):
        lat, lng = hex_to_latlng(coord)
        assert latlng_to_hex(lat, lng) == coord, f"round trip failed for {coord}"
