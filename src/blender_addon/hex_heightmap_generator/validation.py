"""Pure validation core (design doc §7.3, §12).

This module is bpy-free. It composes the parser, the plane->pixel
mapping, the hex-footprint bounds check, and name-collision detection
into a structured list of issues. Preflight runs the full batch before
any geometry is created; any error blocks generation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .coordinates import (
    CubeCoord,
    HexOrientation,
    Issue,
    cube_to_plane,
    parse_cube_coords,
)
from .naming import label_string, tile_object_name
from .sampling import is_in_bounds

_SQRT3: float = 3.0**0.5


@dataclass(frozen=True)
class MappingParams:
    """Raster mapping parameters (design doc §6.6, §7.3)."""

    raster_origin_x: float
    raster_origin_y: float
    pixels_per_unit_x: float
    pixels_per_unit_y: float
    raster_y_sign: float
    hex_radius: float
    orientation: HexOrientation


def plane_to_pixel(
    plane_x: float, plane_y: float, params: MappingParams
) -> tuple[float, float]:
    """Convert a logical map-plane position to raster pixel coordinates.

    pixel_x = origin_x + x * ppu_x
    pixel_y = origin_y + y * ppu_y * y_sign
    (design doc §7.3).
    """
    u: float = params.raster_origin_x + plane_x * params.pixels_per_unit_x
    v: float = (
        params.raster_origin_y
        + plane_y * params.pixels_per_unit_y * params.raster_y_sign
    )
    return u, v


def hex_footprint_extent(
    orientation: HexOrientation, hex_radius: float
) -> tuple[float, float]:
    """Return the (half_x, half_y) bounding extent of one hex footprint.

    Pointy-top: half_x = R*sqrt(3)/2, half_y = R.
    Flat-top:   half_x = R, half_y = R*sqrt(3)/2.
    """
    if orientation is HexOrientation.POINTY:
        return hex_radius * _SQRT3 / 2.0, hex_radius
    return hex_radius, hex_radius * _SQRT3 / 2.0


def _coord_in_bounds(
    coord: CubeCoord,
    raster_width: int,
    raster_height: int,
    params: MappingParams,
) -> bool:
    """Return True if the whole hex footprint samples inside the raster."""
    center_x, center_y = cube_to_plane(coord, params.orientation, params.hex_radius)
    half_x, half_y = hex_footprint_extent(params.orientation, params.hex_radius)
    for dx in (-half_x, half_x):
        for dy in (-half_y, half_y):
            u, v = plane_to_pixel(center_x + dx, center_y + dy, params)
            if not is_in_bounds(u, v, raster_width, raster_height):
                return False
    return True


def validate_batch(
    text: str,
    raster_width: int,
    raster_height: int,
    params: MappingParams,
    existing_names: set[str],
) -> list[Issue]:
    """Preflight a full batch; return all issues (empty means OK).

    Composes: coordinate parsing, per-coordinate raster-bounds checks
    (no silent clamping), and generated-name collision detection.
    """
    coords, issues = parse_cube_coords(text)
    if issues:
        return issues

    for coord in coords:
        if not _coord_in_bounds(coord, raster_width, raster_height, params):
            issues.append(
                Issue(
                    "error",
                    "SAMPLE_OUT_OF_BOUNDS",
                    f"Coordinate {label_string(coord)} samples outside the "
                    f"raster bounds; adjust mapping or raster",
                )
            )
        name: str = tile_object_name(coord)
        if name in existing_names:
            issues.append(
                Issue(
                    "error",
                    "NAME_COLLISION",
                    f"An object named {name} already exists; not overwriting",
                )
            )
    return issues
