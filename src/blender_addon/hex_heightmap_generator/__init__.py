"""Hex Heightmap Generator — Blender extension.

Batch-generate printable heightmapped hex tiles from a user-authored
template, a local heightmap raster, and a list of cube coordinates.

v0.1 proof of concept: deterministic duplication + raster sampling +
Z deformation + Boolean engraving while preserving the base mesh.

This package init is a lazy registration shim: it does NOT import bpy at
module level, so the pure core modules (coordinates, sampling, naming,
validation) can be imported and unit-tested with normal Python outside
Blender. bpy-dependent modules are imported only inside register().
"""

from __future__ import annotations

from typing import Any


def _import_bpy_modules() -> list[Any]:
    """Import bpy-dependent submodules in registration order.

    Imported lazily so that importing a pure submodule (e.g.
    ``hex_heightmap_generator.coordinates``) never pulls in bpy.
    """
    from hex_heightmap_generator import operators_hello  # noqa: PLC0415

    return [operators_hello]


def register() -> None:
    """Register all extension classes (operators, properties, panels)."""
    for module in _import_bpy_modules():
        module.register()


def unregister() -> None:
    """Unregister all extension classes in reverse registration order."""
    for module in reversed(_import_bpy_modules()):
        module.unregister()
