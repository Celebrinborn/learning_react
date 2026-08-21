"""Hello-world operator proving the extension toolchain end-to-end.

This is a permanent, trivial operator used to verify that the extension
registers and executes inside Blender. It is isolated from the pure core
modules so they remain importable without bpy.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none

from __future__ import annotations

import bpy
from bpy.types import Operator as OperatorType


class HexgenHelloWorld(OperatorType):
    """Trivial operator proving the extension toolchain (hello world)."""

    bl_idname: str = "hexgen.hello_world"
    bl_label: str = "Hex Generator: Hello World"
    bl_description: str = "Records a hello-world outcome on the scene"
    bl_undo: str = "Hex Generator Hello World"

    def execute(self, context: bpy.types.Context) -> set[str]:
        context.scene["hg_hello"] = "world"
        return {"FINISHED"}


classes: tuple[type[OperatorType], ...] = (HexgenHelloWorld,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
