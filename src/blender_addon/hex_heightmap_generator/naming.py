"""Deterministic object/collection naming (design doc §6.5, §10).

This module is bpy-free. Object names are deterministic from q,r,s with
explicit signs (positive/zero -> '+', negative -> '-'), e.g.
``HG_q+2_r-1_s-1``. The canonical label string is plain comma-separated
integers, e.g. ``2,-1,-1``.
"""

from __future__ import annotations

from .coordinates import CubeCoord

# Scene-contract constants (design doc §5).
GROUP_TERRAIN_SURFACE: str = "HG_TERRAIN_SURFACE"
COLLECTION_GENERATED: str = "HG_GENERATED"
ROLE_TEMPLATE: str = "template"
ROLE_LABEL_ANCHOR: str = "label_anchor"
ROLE_GENERATED_TILE: str = "generated_tile"

# Custom property names on generated tiles (design doc §10).
PROP_Q: str = "hg_q"
PROP_R: str = "hg_r"
PROP_S: str = "hg_s"
PROP_SOURCE_TEMPLATE: str = "hg_source_template"
PROP_ROLE: str = "hg_role"


def _signed(value: int) -> str:
    """Format an integer with an explicit sign: +2, -1, +0."""
    return f"+{value}" if value >= 0 else f"{value}"


def tile_object_name(coord: CubeCoord) -> str:
    """Deterministic generated-tile object name, e.g. HG_q+2_r-1_s-1."""
    return f"HG_q{_signed(coord.q)}_r{_signed(coord.r)}_s{_signed(coord.s)}"


def label_string(coord: CubeCoord) -> str:
    """Canonical engraved label, e.g. 2,-1,-1 (plain integers)."""
    return f"{coord.q},{coord.r},{coord.s}"
