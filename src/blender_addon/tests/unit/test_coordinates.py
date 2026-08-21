"""Border tests for cube/axial-to-plane coordinate transforms (design doc §7).

Fixture values are computed by hand from the §7.2 formulas with hex
radius R = 1:

Pointy-top:  x = R*sqrt(3)*(q + r/2);  y = R*3/2*r
Flat-top:    x = R*3/2*q;              y = R*sqrt(3)*(r + q/2)
"""

from __future__ import annotations

import math

from hex_heightmap_generator.coordinates import (
    CubeCoord,
    HexOrientation,
    cube_to_plane,
)

SQRT3: float = math.sqrt(3.0)


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


def test_pointy_origin_maps_to_origin() -> None:
    x, y = cube_to_plane(CubeCoord(0, 0, 0), HexOrientation.POINTY, 1.0)
    assert _close(x, 0.0)
    assert _close(y, 0.0)


def test_pointy_known_fixtures() -> None:
    cases: list[tuple[CubeCoord, float, float]] = [
        (CubeCoord(1, 0, -1), SQRT3, 0.0),
        (CubeCoord(0, 1, -1), SQRT3 / 2.0, 1.5),
        (CubeCoord(1, -1, 0), SQRT3 / 2.0, -1.5),
        (CubeCoord(2, -1, -1), 1.5 * SQRT3, -1.5),
        (CubeCoord(-1, 1, 0), -SQRT3 / 2.0, 1.5),
    ]
    for coord, expected_x, expected_y in cases:
        x, y = cube_to_plane(coord, HexOrientation.POINTY, 1.0)
        assert _close(x, expected_x), f"{coord}: x={x} != {expected_x}"
        assert _close(y, expected_y), f"{coord}: y={y} != {expected_y}"


def test_flat_known_fixtures() -> None:
    # Flat-top (R=1): x = 1.5*q; y = sqrt(3)*(r + q/2)
    cases: list[tuple[CubeCoord, float, float]] = [
        (CubeCoord(1, 0, -1), 1.5, SQRT3 / 2.0),
        (CubeCoord(0, 1, -1), 0.0, SQRT3),
        (CubeCoord(1, -1, 0), 1.5, -SQRT3 / 2.0),
        (CubeCoord(2, -1, -1), 3.0, 0.0),
        (CubeCoord(-1, 0, 1), -1.5, -SQRT3 / 2.0),
    ]
    for coord, expected_x, expected_y in cases:
        x, y = cube_to_plane(coord, HexOrientation.FLAT, 1.0)
        assert _close(x, expected_x), f"{coord}: x={x} != {expected_x}"
        assert _close(y, expected_y), f"{coord}: y={y} != {expected_y}"


def test_radius_scales_the_plane() -> None:
    x1, y1 = cube_to_plane(CubeCoord(1, 0, -1), HexOrientation.POINTY, 1.0)
    x2, y2 = cube_to_plane(CubeCoord(1, 0, -1), HexOrientation.POINTY, 2.5)
    assert _close(x2, x1 * 2.5)
    assert _close(y2, y1 * 2.5)


def test_adjacent_hex_centers_are_one_spacing_apart() -> None:
    """Two adjacent pointy-top centers are exactly sqrt(3)*R apart."""
    a = cube_to_plane(CubeCoord(0, 0, 0), HexOrientation.POINTY, 1.0)
    b = cube_to_plane(CubeCoord(1, 0, -1), HexOrientation.POINTY, 1.0)
    distance: float = math.hypot(b[0] - a[0], b[1] - a[1])
    assert _close(distance, SQRT3)
