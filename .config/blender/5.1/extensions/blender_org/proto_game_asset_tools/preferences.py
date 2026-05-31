# PROTO Game Asset Tools
# 2025 PROTOWLF, Licensed under GPL-3.0

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty


def update_prototools_panel_category():
    from .src.ui import panel_classes
    
    settings = bpy.context.preferences.addons[__package__].preferences
    
    for panel_class in panel_classes:
        try:
            bpy.utils.unregister_class(panel_class)
        except:
            pass
    
        panel_class.bl_category = 'PROTO'
        if settings.viewport_panel_category == 'GAME_ASSETS':
            panel_class.bl_category = 'Game Asset Tools'
        elif settings.viewport_panel_category == 'CUSTOM':
            if settings.custom_viewport_panel_category == '':
                panel_class.bl_category = 'Game Asset Tools'
            else:
                panel_class.bl_category = settings.custom_viewport_panel_category
    
        bpy.utils.register_class(panel_class)


# Addon prefs
class ProtoGameAssetToolsPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    action_slot_behavior: EnumProperty(
        name="Action Slot Behavior",
        items=(
            ("ARMATURE_NAME", "Use Armature Name", "Add-on will expect Actions to have a Slot with the same name as your Armature"),
            ("MANUAL", "Manually Set Slots", "Manually manage Action Slots yourself")
        ),
        default='ARMATURE_NAME',
        description="How to handle Action Slots"
    )
    
    def viewport_panel_category_update(self, context):
        update_prototools_panel_category()
    
    viewport_panel_category: EnumProperty(
        name="Viewport Panel Category",
        items=(
            ("PROTO", "'PROTO'", "Add-on will use the viewport panel category 'PROTO'."),
            ("GAME_ASSETS", "'Game Asset Tools'", "Add-on will use the viewport panel category 'Game Asset Tools'."),
            ("CUSTOM", "Custom", "Add-on will use a custom viewport panel category.")
        ),
        default='GAME_ASSETS',
        description="What Viewport panel category to use for this add-on",
        update=viewport_panel_category_update
    )
    
    def custom_viewport_panel_category_update(self, context):
        update_prototools_panel_category()
    
    custom_viewport_panel_category: StringProperty(
        name="Custom Name",
        description="custom name for the add-on's viewport panel category",
        default="Custom Category",
        update=custom_viewport_panel_category_update
    )

    def draw(self, context):
        layout = self.layout
        
        if bpy.app.version >= (4, 4, 0):
            # Blender 4.4 and up
            layout = self.layout
            layout.label(text="This add-on expects a given Armature to use exactly one (1) Slot per-Action.", icon="INFO")
            layout.label(text="Action Slot Behavior:") # icon="ACTION_SLOT"
            row = layout.row()
            row.prop(self, "action_slot_behavior", expand=True)
        
        layout.label(text="Viewport Panel Category:") # icon="ACTION_SLOT"
        row = layout.row()
        row.prop(self, "viewport_panel_category", expand=True)
        if self.viewport_panel_category == 'CUSTOM':
            layout.prop(self, "custom_viewport_panel_category")


def register():
    bpy.utils.register_class(ProtoGameAssetToolsPrefs)
    

def unregister():
    bpy.utils.unregister_class(ProtoGameAssetToolsPrefs)
