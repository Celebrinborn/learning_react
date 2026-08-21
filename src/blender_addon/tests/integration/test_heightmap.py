"""Border tests for heightmap loading (design doc §6.4).

Asserts outcomes: the loaded normalized grid matches the known synthetic
gradient at sampled pixels, and an RGB image whose channels disagree is
rejected. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportMissingParameterType=none

from __future__ import annotations

import math
from pathlib import Path
import tempfile

import bpy

from hex_heightmap_generator.heightmap import HeightmapError, load_heightmap
from tests.integration import fixture_builder as fx


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-3, abs_tol=1e-3)


def test_load_gradient_matches_known_values() -> None:
    fx.cleanup_scene()
    tmp_dir: Path = Path(tempfile.mkdtemp(prefix="hg_test_"))
    png: Path = tmp_dir / "gradient.png"
    fx.build_gradient_heightmap(png)

    hm = load_heightmap(str(png))
    assert hm.width == fx.GRADIENT_WIDTH
    assert hm.height == fx.GRADIENT_HEIGHT

    # Pixel (u, v) value = round(u/(W-1)*255)/255.
    for u, v in [(0, 0), (0, 50), (99, 0), (50, 25), (10, 90)]:
        expected: float = round(u / (fx.GRADIENT_WIDTH - 1) * 255) / 255.0
        actual: float = hm.grid[v * hm.width + u]
        assert _close(actual, expected), f"pixel ({u},{v}): {actual} != {expected}"


def test_rgb_channels_must_agree() -> None:
    fx.cleanup_scene()
    tmp_dir: Path = Path(tempfile.mkdtemp(prefix="hg_test_"))
    png: Path = tmp_dir / "bad_rgb.png"
    # Build an RGB image where R != G (should be rejected).
    image: bpy.types.Image = bpy.data.images.new(
        name="bad_rgb", width=4, height=4, alpha=False
    )
    pixels: list[float] = [0.0] * (4 * 4 * 4)
    for i in range(16):
        pixels[i * 4] = 1.0  # R
        pixels[i * 4 + 1] = 0.0  # G (differs from R)
        pixels[i * 4 + 2] = 1.0  # B
        pixels[i * 4 + 3] = 1.0
    image.pixels = pixels
    image.filepath_raw = str(png)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)

    try:
        load_heightmap(str(png))
    except HeightmapError:
        pass
    else:
        raise AssertionError("expected HeightmapError for R != G")
