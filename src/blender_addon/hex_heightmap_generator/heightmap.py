"""Heightmap raster loading (design doc §6.4).

Loads a local grayscale/RGB raster as a Blender Image datablock, bulk-reads
the pixels once, verifies the channels are grayscale (R == G == B within
tolerance), and returns a flat normalized [0,1] grid. The source Image
datablock is never resized or resampled.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

from dataclasses import dataclass

import bpy

# Tolerance for treating an RGB image as grayscale (R == G == B).
GRAYSCALE_TOLERANCE: float = 1.0 / 255.0


class HeightmapError(Exception):
    """Raised when a heightmap raster cannot be loaded or is invalid."""


@dataclass
class Heightmap:
    """A loaded, normalized heightmap raster."""

    width: int
    height: int
    grid: list[float]  # flat row-major, normalized [0,1]


def load_heightmap(path: str) -> Heightmap:
    """Load a local raster and return its normalized [0,1] grid.

    Raises HeightmapError if the file cannot be loaded or if the image is
    not grayscale (R, G, B disagree beyond tolerance).
    """
    try:
        image: bpy.types.Image = bpy.data.images.load(path, check_existing=True)
    except RuntimeError as exc:
        raise HeightmapError(f"cannot load heightmap: {path}") from exc

    # Treat the raster as data, not display color.
    try:
        image.colorspace_settings.name = "Non-Color"
    except (TypeError, AttributeError):
        pass  # colorspace not settable for this image type

    width: int = image.size[0]
    height: int = image.size[1]
    if width <= 0 or height <= 0:
        raise HeightmapError(f"invalid raster size {width}x{height}")

    pixels: list[float] = list(image.pixels)
    expected: int = width * height * 4
    if len(pixels) != expected:
        raise HeightmapError(
            f"pixel buffer size {len(pixels)} != expected {expected}"
        )

    grid: list[float] = [0.0] * (width * height)
    for i in range(width * height):
        r: float = pixels[i * 4]
        g: float = pixels[i * 4 + 1]
        b: float = pixels[i * 4 + 2]
        if (
            abs(r - g) > GRAYSCALE_TOLERANCE
            or abs(r - b) > GRAYSCALE_TOLERANCE
        ):
            raise HeightmapError(
                f"pixel ({i % width}, {i // width}) is not grayscale "
                f"(R={r:.4f}, G={g:.4f}, B={b:.4f})"
            )
        grid[i] = r

    return Heightmap(width=width, height=height, grid=grid)
