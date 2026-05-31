bl_info = {
    "name": "Quick Character Selector",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 1, 0),
    "author": "Matias Martin 3D",
    "description": "Permite seleccionar armatures rápidamente y dirigir la cámara a ellos."
}

import bpy

class ArmatureProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

class SceneProperties(bpy.types.PropertyGroup):
    armatures: bpy.props.CollectionProperty(type=ArmatureProperty)

class QuickCharacterSelectorPanel(bpy.types.Panel):
    bl_label = "Character Selector"
    bl_idname = "OBJECT_PT_quick_character_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Quick Selector'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.scale_x = 1.5
        row.scale_y = 1.5
        row.operator("object.add_armature_button", text="Add Armature Button")
        
        for armature in scene.quick_character_selector.armatures:
            row = layout.row()
            row.scale_x = 1.5
            row.scale_y = 1.5
            op = row.operator("view3d.view_armature", text=armature.name)
            op.name = armature.name
            
            remove_op = row.operator("object.remove_armature", text="", icon="X")
            remove_op.name = armature.name

class AddArmatureButtonOperator(bpy.types.Operator):
    bl_idname = "object.add_armature_button"
    bl_label = "Add Armature Button"
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            if obj.type == 'ARMATURE' and obj.name not in [armature.name for armature in context.scene.quick_character_selector.armatures]:
                new_armature = context.scene.quick_character_selector.armatures.add()
                new_armature.name = obj.name
        return {'FINISHED'}

class ViewArmatureOperator(bpy.types.Operator):
    bl_idname = "view3d.view_armature"
    bl_label = "View Armature"
    
    name: bpy.props.StringProperty()
    
    def execute(self, context):
        obj = bpy.data.objects[self.name]
        
        bpy.ops.object.select_all(action='DESELECT')
        
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.view3d.view_selected(use_all_regions=False)
        
        return {'FINISHED'}

class RemoveArmatureOperator(bpy.types.Operator):
    bl_idname = "object.remove_armature"
    bl_label = "Remove Armature"
    
    name: bpy.props.StringProperty()
    
    def execute(self, context):
        armatures = context.scene.quick_character_selector.armatures
        for i, armature in enumerate(armatures):
            if armature.name == self.name:
                armatures.remove(i)
                break
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ArmatureProperty)
    bpy.utils.register_class(SceneProperties)
    bpy.types.Scene.quick_character_selector = bpy.props.PointerProperty(type=SceneProperties)
    bpy.utils.register_class(QuickCharacterSelectorPanel)
    bpy.utils.register_class(AddArmatureButtonOperator)
    bpy.utils.register_class(ViewArmatureOperator)
    bpy.utils.register_class(RemoveArmatureOperator)

def unregister():
    bpy.utils.unregister_class(ArmatureProperty)
    bpy.utils.unregister_class(SceneProperties)
    del bpy.types.Scene.quick_character_selector
    bpy.utils.unregister_class(QuickCharacterSelectorPanel)
    bpy.utils.unregister_class(AddArmatureButtonOperator)
    bpy.utils.unregister_class(ViewArmatureOperator)
    bpy.utils.unregister_class(RemoveArmatureOperator)

if __name__ == "__main__":
    register()