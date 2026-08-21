"""Border tests for the N-panel (design doc §11).

Asserts outcomes: the extension registers a "Hex Generator" panel in the
3D Viewport sidebar, and the panel's draw() runs against a live scene
without raising. Run via the Blender background harness.
"""

# pyright: reportMissingImports=none, reportMissingModuleSource=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none, reportUnknownParameterType=none, reportUntypedBaseClass=none, reportOptionalMemberAccess=none, reportOptionalSubscript=none

from __future__ import annotations

import bpy


def test_panel_registered_in_viewport_sidebar() -> None:
    # Blender exposes registered classes on bpy.types by bl_idname.
    panel_cls = bpy.types.VIEW3D_PT_hexgen
    assert panel_cls.bl_idname == "VIEW3D_PT_hexgen"
    assert panel_cls.bl_space_type == "VIEW_3D"
    assert panel_cls.bl_region_type == "UI"
    assert panel_cls.bl_category == "Hex Generator"


def test_panel_draws_against_live_scene() -> None:
    """draw() must not raise on a scene with default settings.

    Registered classes cannot be instantiated directly in Blender 5.x,
    so draw() is invoked unbound with a stand-in self exposing .layout.
    """
    panel_cls = bpy.types.VIEW3D_PT_hexgen
    panel_cls.draw(_FakePanel(), bpy.context)


class _FakePanel:
    """Minimal stand-in for a Panel instance: exposes .layout."""

    def __init__(self) -> None:
        self.layout = _FakeLayout()


class _FakeLayout:
    """Minimal stand-in for a UI layout: absorbs any call/attribute."""

    def __call__(self, *args: object, **kwargs: object) -> "_FakeLayout":
        return self

    def __getattr__(self, name: str) -> "_FakeLayout":
        if name.startswith("__"):
            raise AttributeError(name)
        return self

    def column(self, *args: object, **kwargs: object) -> "_FakeLayout":
        return self

    def row(self, *args: object, **kwargs: object) -> "_FakeLayout":
        return self

    def label(self, *args: object, **kwargs: object) -> "_FakeLayout":
        return self

    def operator(self, *args: object, **kwargs: object) -> "_FakeLayout":
        return self
