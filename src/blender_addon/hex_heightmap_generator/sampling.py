"""Pure bilinear height sampling (design doc §6.4, §19.1).

This module is bpy-free so it can be unit-tested with normal Python.
It operates on a flat, row-major grid of normalized [0,1] height values.
Integer (u, v) coordinates address pixel centers; sub-pixel coordinates
are bilinearly interpolated. Out-of-bounds samples raise a structured
error rather than clamping silently (design doc §12).
"""

from __future__ import annotations

import math


class SampleOutOfBoundsError(Exception):
    """Raised when a sample address falls outside the raster bounds.

    Carries the offending address and the raster dimensions so callers
    can report which coordinate(s) are affected (design doc §12).
    """

    def __init__(self, u: float, v: float, width: int, height: int) -> None:
        self.u: float = u
        self.v: float = v
        self.width: int = width
        self.height: int = height
        super().__init__(
            f"sample ({u}, {v}) is outside raster bounds "
            f"[0, {width - 1}] x [0, {height - 1}]"
        )


def is_in_bounds(u: float, v: float, width: int, height: int) -> bool:
    """Return True if (u, v) addresses a valid pixel-center region.

    Valid addresses satisfy 0 <= u <= width-1 and 0 <= v <= height-1.
    """
    return 0.0 <= u <= float(width - 1) and 0.0 <= v <= float(height - 1)


def bilinear_sample(
    grid: list[float], width: int, height: int, u: float, v: float
) -> float:
    """Bilinearly sample a normalized [0,1] value at (u, v).

    ``grid`` is flat row-major with ``width * height`` entries. (u, v)
    are in pixel units where integer values address pixel centers.
    Raises SampleOutOfBoundsError if the address is outside the raster.
    """
    if not is_in_bounds(u, v, width, height):
        raise SampleOutOfBoundsError(u, v, width, height)

    x0: int = math.floor(u)
    y0: int = math.floor(v)
    x1: int = min(x0 + 1, width - 1)
    y1: int = min(y0 + 1, height - 1)
    fx: float = u - float(x0)
    fy: float = v - float(y0)

    top_left: float = grid[y0 * width + x0]
    top_right: float = grid[y0 * width + x1]
    bottom_left: float = grid[y1 * width + x0]
    bottom_right: float = grid[y1 * width + x1]

    top: float = top_left + (top_right - top_left) * fx
    bottom: float = bottom_left + (bottom_right - bottom_left) * fx
    return top + (bottom - top) * fy


def normalized_to_elevation(
    normalized: float, elevation_offset_mm: float, elevation_range_mm: float
) -> float:
    """Convert a normalized [0,1] sample to a physical elevation in mm.

    height_mm = elevation_offset_mm + normalized * elevation_range_mm
    (design doc §6.4).
    """
    return elevation_offset_mm + normalized * elevation_range_mm
