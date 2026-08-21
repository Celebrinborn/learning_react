"""Hex Heightmap Generator — Blender extension.

Batch-generate printable heightmapped hex tiles from a user-authored
template, a local heightmap raster, and a list of cube coordinates.

v0.1 proof of concept: deterministic duplication + raster sampling +
Z deformation + Boolean engraving while preserving the base mesh.

This package init is a lazy registration shim: it does NOT import bpy at
module level, so the pure core modules (coordinates, sampling, naming,
validation) can be imported and unit-tested with normal Python outside
Blender. bpy-dependent modules are imported only inside register().

The package uses RELATIVE imports throughout: Blender loads extensions as a
nested package (bl_ext.user_default.<id>), so absolute self-imports of the
form ``from hex_heightmap_generator.X import ...`` would fail with
``No module named 'hex_heightmap_generator'``.
"""

from __future__ import annotations

from typing import Any


def _import_bpy_modules() -> list[Any]:
    """Import bpy-dependent submodules in registration order.

    Imported lazily so that importing a pure submodule (e.g.
    ``hex_heightmap_generator.coordinates``) never pulls in bpy.
    """
    from . import (  # noqa: PLC0415
        operators_generate,
        operators_hello,
        operators_setup,
        properties,
        ui,
    )

    # properties first: the generate operator reads scene.hg_settings.
    # ui last: the panel binds to operators and settings.
    return [
        properties,
        operators_hello,
        operators_setup,
        operators_generate,
        ui,
    ]


def register() -> None:
    """Register all extension classes (operators, properties, panels)."""
    for module in _import_bpy_modules():
        module.register()


def unregister() -> None:
    """Unregister all extension classes in reverse registration order."""
    for module in reversed(_import_bpy_modules()):
        module.unregister()
