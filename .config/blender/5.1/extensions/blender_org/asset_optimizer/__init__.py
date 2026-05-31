import bpy
from . import operators
from . import ui
from . import utils


def register():
    """Register all addon classes and properties"""
    utils.register()
    operators.register()
    ui.register()


def unregister():
    """Unregister all addon classes and properties"""
    ui.unregister()
    operators.unregister()
    utils.unregister()


if __name__ == "__main__":
    register()
