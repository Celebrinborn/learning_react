"""Hello-world integration test: proves the Blender 5.x toolchain end-to-end.

Border/outcome assertions only:
- The extension registers (importable, operators present in bpy.ops).
- The trivial operator executes and its observable outcome is recorded
  (scene custom property hg_hello == "world").
- The manifest declares the 5.x minimum version.

Run via: blender --background --python scripts/run_integration.py
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnusedImport=none

from __future__ import annotations

from pathlib import Path

import bpy


def test_extension_registers() -> None:
    """The extension module imports and its operator is registered in bpy.ops."""
    import hex_heightmap_generator  # noqa: F401  (module must import cleanly)

    assert hasattr(bpy.ops.hexgen, "hello_world"), (
        "bpy.ops.hexgen.hello_world operator is not registered"
    )


def test_manifest_declares_blender_5_min() -> None:
    """The installed manifest declares blender_version_min in the 5.x line."""
    import hex_heightmap_generator as module

    manifest_path = Path(module.__file__).with_name("blender_manifest.toml")
    assert manifest_path.is_file(), f"manifest missing: {manifest_path}"
    text: str = manifest_path.read_text(encoding="utf-8")
    assert 'blender_version_min = "5.0.0"' in text, (
        "manifest must declare blender_version_min = \"5.0.0\""
    )


def test_hello_world_operator_sets_scene_property() -> None:
    """Running the operator records its observable outcome on the scene."""
    scene = bpy.context.scene
    scene["hg_hello"] = ""  # reset observable state
    result = bpy.ops.hexgen.hello_world()
    assert "CANCELLED" not in result, "operator returned CANCELLED"
    assert scene["hg_hello"] == "world", (
        f"expected scene['hg_hello'] == 'world', got {scene['hg_hello']!r}"
    )
