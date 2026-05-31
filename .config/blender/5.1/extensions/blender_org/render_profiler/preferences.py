import bpy  # type: ignore
from bpy.props import IntProperty  # type: ignore
from bpy.types import AddonPreferences  # type: ignore


def get_report_font_size() -> float:
    """Return report font size (pixels) from add-on preferences."""
    try:
        addon = bpy.context.preferences.addons.get(__package__)
        if addon and getattr(addon, "preferences", None):
            return int(getattr(addon.preferences, "font_size", 14))
    except Exception:
        pass
    return 14


class render_profiler_addon_preferences(AddonPreferences):
    bl_idname = __package__

    font_size: IntProperty(
        name="Report font size",
        subtype="PIXEL",
        default=14,
        min=8,
        max=24,
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Reopen report window to see the effect")
        layout.prop(self, "font_size")


# Registration
def register():
    bpy.utils.register_class(render_profiler_addon_preferences)

def unregister():
    bpy.utils.unregister_class(render_profiler_addon_preferences)