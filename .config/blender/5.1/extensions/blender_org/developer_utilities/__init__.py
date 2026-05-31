from . import edit_operator_source
from . import edit_addon_source
from . import python_text_api_lookup
from . import document_addon
import bpy 
from bpy.props import BoolProperty, StringProperty, IntProperty
from bpy.types import AddonPreferences

class Pid():
    pid = -1

class DeveloperUtilitiesPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    use_external : BoolProperty(
            name="Use External Editor",
            default=False,
            )
    
    target_dir : StringProperty(
            name="Target Directory",
            subtype='DIR_PATH',
            )
    
    use_server : BoolProperty(
            name="Start HTTP Server",
            default=False,
            )
    
    server_port : IntProperty(
            name="Server Port",
            default=8000,
            min = 0,
            max = 65535,
            )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Edit Addon Options")
        box.prop(self, "use_external")
        box = layout.box()
        box.label(text="Generate Documentation Options")
        box.prop(self, "target_dir")
        row = box.row()
        row.prop(self, "use_server")
        row.prop(self, "server_port")

def register():
    bpy.utils.register_class(DeveloperUtilitiesPreferences)
    document_addon.register()
    edit_operator_source.register()
    edit_addon_source.register()
    python_text_api_lookup.register()

def unregister():
    edit_operator_source.unregister()
    edit_addon_source.unregister()
    python_text_api_lookup.unregister()
    document_addon.unregister()
    bpy.utils.unregister_class(DeveloperUtilitiesPreferences)
    
