# ruff: noqa: E402, I001

# Import / reload local modules (Required when using bpy.ops.scripts.reload()
# a.k.a. the "Reload Scripts" operator in Blender.

_needs_reload: bool = "bpy" in locals()

import bpy  # noqa: F401

from . import (
    gui,
    operators,
    pole_angle,
)

if _needs_reload:
    import importlib

    importlib.reload(gui)
    importlib.reload(operators)
    importlib.reload(pole_angle)


def register() -> None:
    operators.register()
    gui.register()


def unregister() -> None:
    operators.unregister()
    gui.unregister()
