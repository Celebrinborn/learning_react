"""Replicate Blender's real extension load to verify the relative-import fix.

Blender loads an installed add-on as a NESTED package
(``bl_ext.user_default.<extension_id>``) and then calls its ``register()``.
The old code used absolute self-imports (``from hex_heightmap_generator.X
import ...``), which only resolve when the package is top-level — so under
Blender's nested load they raised ``No module named 'hex_heightmap_generator'``.

This script rebuilds the nested structure from the source package and imports
it under a nested name, then calls register(). A unique base namespace
(``hg_verify_pkg``) is used so we never accidentally import Blender's real
``bl_ext`` tree or a stale installed copy. The failure mode being tested
(absolute self-import under a nested namespace) is identical regardless of the
base name.

Usage (from src/blender_addon):
    blender --background --python scripts/verify_bl_ext_load.py
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

import importlib
from pathlib import Path
import shutil
import sys
import tempfile

ADDON_ROOT: Path = Path(__file__).resolve().parent.parent
SRC_PKG: Path = ADDON_ROOT / "hex_heightmap_generator"
EXT_ID: str = "hex_heightmap_generator"


def main() -> int:
    tmp: Path = Path(tempfile.mkdtemp(prefix="bl_ext_verify_"))
    try:
        # Build the nested package layout Blender uses, under a unique base
        # namespace so we never collide with Blender's real bl_ext tree:
        #   <tmp>/hg_verify_pkg/user_default/<ext_id>/...
        base: Path = tmp / "hg_verify_pkg" / "user_default"
        base.mkdir(parents=True)
        dest: Path = base / EXT_ID
        shutil.copytree(SRC_PKG, dest)
        # hg_verify_pkg and user_default are namespace packages (no __init__.py).
        sys.path.insert(0, str(tmp))

        module_name: str = f"hg_verify_pkg.user_default.{EXT_ID}"
        module = importlib.import_module(module_name)
        print(f"Imported {module_name}")

        module.register()
        print("register() OK")

        import bpy  # noqa: PLC0415

        # Confirm the panel + an operator actually registered.
        has_panel: bool = hasattr(bpy.types, "VIEW3D_PT_hexgen")
        has_op: bool = hasattr(bpy.ops, "hexgen")
        print(f"panel registered: {has_panel}")
        print(f"operator namespace registered: {has_op}")

        module.unregister()
        print("unregister() OK")

        if has_panel and has_op:
            print("BL_EXT LOAD: PASS")
            return 0
        print("BL_EXT LOAD: FAIL (classes missing after register)")
        return 1
    except Exception:  # noqa: BLE001
        import traceback  # noqa: PLC0415

        traceback.print_exc()
        print("BL_EXT LOAD: FAIL (exception)")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
