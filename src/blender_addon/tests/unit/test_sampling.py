"""Border tests for the bilinear height sampler (design doc §6.4, §19.1).

The sampler is bpy-free: it operates on a flat, row-major, normalized
[0,1] grid. Integer (u, v) address pixel centers. Out-of-bounds samples
raise a structured error rather than clamping.
"""

from __future__ import annotations

import math

from hex_heightmap_generator.sampling import (
    SampleOutOfBoundsError,
    bilinear_sample,
    is_in_bounds,
    normalized_to_elevation,
)


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


# 2x2 grid, row-major: [[1, 2], [3, 4]]
GRID: list[float] = [1.0, 2.0, 3.0, 4.0]
WIDTH: int = 2
HEIGHT: int = 2


def test_exact_corner_pixels() -> None:
    assert _close(bilinear_sample(GRID, WIDTH, HEIGHT, 0.0, 0.0), 1.0)
    assert _close(bilinear_sample(GRID, WIDTH, HEIGHT, 1.0, 0.0), 2.0)
    assert _close(bilinear_sample(GRID, WIDTH, HEIGHT, 0.0, 1.0), 3.0)
    assert _close(bilinear_sample(GRID, WIDTH, HEIGHT, 1.0, 1.0), 4.0)


def test_center_midpoint_is_average_of_four() -> None:
    value: float = bilinear_sample(GRID, WIDTH, HEIGHT, 0.5, 0.5)
    assert _close(value, (1.0 + 2.0 + 3.0 + 4.0) / 4.0)


def test_edge_midpoint_is_average_of_two() -> None:
    value: float = bilinear_sample(GRID, WIDTH, HEIGHT, 0.5, 0.0)
    assert _close(value, (1.0 + 2.0) / 2.0)


def test_out_of_bounds_raises_structured_error() -> None:
    for u, v in [(-0.1, 0.0), (WIDTH, 0.0), (0.0, HEIGHT), (0.0, -0.5)]:
        try:
            bilinear_sample(GRID, WIDTH, HEIGHT, u, v)
        except SampleOutOfBoundsError as exc:
            assert exc.u == u
            assert exc.v == v
            assert exc.width == WIDTH
            assert exc.height == HEIGHT
        else:
            raise AssertionError(f"expected OOB error for ({u}, {v})")


def test_is_in_bounds() -> None:
    assert is_in_bounds(0.0, 0.0, WIDTH, HEIGHT)
    assert is_in_bounds(1.0, 1.0, WIDTH, HEIGHT)
    assert is_in_bounds(0.5, 0.5, WIDTH, HEIGHT)
    assert not is_in_bounds(-0.001, 0.0, WIDTH, HEIGHT)
    assert not is_in_bounds(WIDTH, 0.0, WIDTH, HEIGHT)
    assert not is_in_bounds(0.0, HEIGHT, WIDTH, HEIGHT)


def test_normalized_to_elevation() -> None:
    # height_mm = offset + normalized * range
    assert _close(normalized_to_elevation(0.0, 0.0, 10.0), 0.0)
    assert _close(normalized_to_elevation(1.0, 0.0, 10.0), 10.0)
    assert _close(normalized_to_elevation(0.5, 0.0, 10.0), 5.0)
    assert _close(normalized_to_elevation(0.0, 2.0, 10.0), 2.0)
    assert _close(normalized_to_elevation(1.0, 2.0, 10.0), 12.0)
