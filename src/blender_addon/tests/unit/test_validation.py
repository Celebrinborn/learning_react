"""Border tests for the pure validation core (design doc §7.3, §12).

Covers the plane->pixel mapping, the hex-footprint bounds check, and
preflight composition (parse + bounds + name collision). Asserts the
structured issues produced, not internal control flow.
"""

from __future__ import annotations

import math

from hex_heightmap_generator.coordinates import HexOrientation
from hex_heightmap_generator.validation import (
    MappingParams,
    hex_footprint_extent,
    plane_to_pixel,
    validate_batch,
)

SQRT3: float = math.sqrt(3.0)


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


def _params(
    origin_x: float = 5.0,
    origin_y: float = 5.0,
    ppu_x: float = 1.0,
    ppu_y: float = 1.0,
    y_sign: float = 1.0,
    radius: float = 1.0,
) -> MappingParams:
    return MappingParams(
        raster_origin_x=origin_x,
        raster_origin_y=origin_y,
        pixels_per_unit_x=ppu_x,
        pixels_per_unit_y=ppu_y,
        raster_y_sign=y_sign,
        hex_radius=radius,
        orientation=HexOrientation.POINTY,
    )


def test_plane_to_pixel_identity() -> None:
    u, v = plane_to_pixel(0.0, 0.0, _params())
    assert _close(u, 5.0)
    assert _close(v, 5.0)


def test_plane_to_pixel_applies_scale_and_origin() -> None:
    params = _params(origin_x=1.0, origin_y=2.0, ppu_x=3.0, ppu_y=4.0)
    u, v = plane_to_pixel(2.0, -1.0, params)
    assert _close(u, 1.0 + 2.0 * 3.0)
    assert _close(v, 2.0 + (-1.0) * 4.0)


def test_plane_to_pixel_y_sign() -> None:
    u_pos, v_pos = plane_to_pixel(0.0, 1.0, _params(y_sign=1.0))
    u_neg, v_neg = plane_to_pixel(0.0, 1.0, _params(y_sign=-1.0))
    assert _close(u_pos, u_neg)
    assert _close(v_pos, 5.0 + 1.0)
    assert _close(v_neg, 5.0 - 1.0)


def test_hex_footprint_extent_pointy() -> None:
    half_x, half_y = hex_footprint_extent(HexOrientation.POINTY, 1.0)
    assert _close(half_x, SQRT3 / 2.0)
    assert _close(half_y, 1.0)


def test_hex_footprint_extent_flat() -> None:
    half_x, half_y = hex_footprint_extent(HexOrientation.FLAT, 1.0)
    assert _close(half_x, 1.0)
    assert _close(half_y, SQRT3 / 2.0)


def test_validate_batch_in_bounds_no_issues() -> None:
    issues = validate_batch("0,0,0", 10, 10, _params(), existing_names=set())
    assert issues == []


def test_validate_batch_out_of_bounds_lists_coordinate() -> None:
    # (10,0,-10) center is far outside a 10x10 raster centered at (5,5).
    issues = validate_batch("10,0,-10", 10, 10, _params(), existing_names=set())
    assert len(issues) == 1
    assert issues[0].code == "SAMPLE_OUT_OF_BOUNDS"
    assert "10,0,-10" in issues[0].message


def test_validate_batch_name_collision() -> None:
    issues = validate_batch(
        "0,0,0", 10, 10, _params(), existing_names={"HG_q+0_r+0_s+0"}
    )
    assert len(issues) == 1
    assert issues[0].code == "NAME_COLLISION"


def test_validate_batch_malformed_line_blocks() -> None:
    issues = validate_batch("1,1,1", 10, 10, _params(), existing_names=set())
    assert len(issues) == 1
    assert issues[0].code == "NONZERO_SUM"


def test_validate_batch_mixed_reports_all() -> None:
    # One OOB coordinate and one name collision in the same batch.
    issues = validate_batch(
        "0,0,0\n10,0,-10",
        10,
        10,
        _params(),
        existing_names={"HG_q+0_r+0_s+0"},
    )
    codes = {issue.code for issue in issues}
    assert "NAME_COLLISION" in codes
    assert "SAMPLE_OUT_OF_BOUNDS" in codes
