import bpy, math
from mathutils import Euler
from .utils import PREVIEW_PREFIX, GEN_PREFIX, get_unit_scale, to_internal, apply_transform, save_params_to_object, cleanup_previews, is_hifi_object, hifi_orphan_cleanup
from .preview_logic import update_preview

class HIFI_OT_generate(bpy.types.Operator):
    bl_idname = "hifi.generate"
    bl_label = "Generate"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scn = context.scene
        hp = scn.hifi_props
        
        previews = [o for o in scn.objects if o.name.startswith(PREVIEW_PREFIX) or o.name.startswith("HIFI_PREV_") or o.name.startswith("hifi_prev_")]
        
        if not previews: 
            self.report({'WARNING'}, "No active preview found.")
            return {'CANCELLED'}
            
        main = previews[0]
        
        try:
            for o in previews:
                raw_name = o.name.replace("HIFI_PREV_", "").replace("hifi_prev_", "").replace(PREVIEW_PREFIX, "")
                o.name = f"{GEN_PREFIX}{raw_name}".lower()
                o["hifi_gen_type"] = hp.generator_type
                
                bpy.ops.object.select_all(action='DESELECT')
                o.select_set(True)
                context.view_layer.objects.active = o
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            
            self.report({'INFO'}, f"Successfully generated: {main.name}")
            hp.generator_type = 'NONE'
            
        except Exception as e:
            self.report({'ERROR'}, "Generation failed.")
            return {'CANCELLED'}
        return {'FINISHED'}

class HIFI_OT_clear_previews(bpy.types.Operator):
    bl_idname = "hifi.clear_previews"
    bl_label = "Clear Previews"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        cleanup_previews()
        context.scene.hifi_props.generator_type = 'NONE'
        self.report({'INFO'}, "Previews cleared.")
        return {'FINISHED'}

class HIFI_OT_join_cleanup(bpy.types.Operator):
    bl_idname = "hifi.join_cleanup"
    bl_label = "Join & Cleanup"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        objs = [o for o in bpy.data.objects if is_hifi_object(o)]
        if not objs: 
            self.report({'WARNING'}, "No objects found to join.")
            return {'CANCELLED'}
            
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        
        try: bpy.ops.object.join()
        except: return {'CANCELLED'}
        
        main = bpy.context.view_layer.objects.active
        main.name = "hifi_combined"
        apply_transform(main)
        
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.0005)
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Meshes joined successfully.")
        except: pass
        return {'FINISHED'}

class HIFI_OT_load_selected_params(bpy.types.Operator):
    bl_idname = "hifi.load_selected_params"
    bl_label = "Load Selected"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return context.active_object is not None
    def execute(self, context):
        obj = context.active_object
        sp = context.scene.hifi_sel_props
        sp.sel_loc_x = obj.location.x; sp.sel_loc_y = obj.location.y; sp.sel_loc_z = obj.location.z
        sp.sel_rot_x_deg = math.degrees(obj.rotation_euler.x); sp.sel_rot_y_deg = math.degrees(obj.rotation_euler.y); sp.sel_rot_z_deg = math.degrees(obj.rotation_euler.z)
        sp.sel_scale_x = obj.scale.x; sp.sel_scale_y = obj.scale.y; sp.sel_scale_z = obj.scale.z
        self.report({'INFO'}, "Parameters loaded.")
        return {'FINISHED'}

class HIFI_OT_apply_transform_to_selected(bpy.types.Operator):
    bl_idname = "hifi.apply_transform_to_selected"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return context.active_object is not None
    def execute(self, context):
        obj = context.active_object
        sp = context.scene.hifi_sel_props
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        try: bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        except: pass
        
        if sp.apply_loc_x: obj.location.x = sp.sel_loc_x
        if sp.apply_loc_y: obj.location.y = sp.sel_loc_y
        if sp.apply_loc_z: obj.location.z = sp.sel_loc_z
        if sp.apply_rot_x: obj.rotation_euler.x = math.radians(sp.sel_rot_x_deg)
        if sp.apply_rot_y: obj.rotation_euler.y = math.radians(sp.sel_rot_y_deg)
        if sp.apply_rot_z: obj.rotation_euler.z = math.radians(sp.sel_rot_z_deg)
        if sp.apply_scale_x: obj.scale.x = sp.sel_scale_x
        if sp.apply_scale_y: obj.scale.y = sp.sel_scale_y
        if sp.apply_scale_z: obj.scale.z = sp.sel_scale_z
        
        self.report({'INFO'}, "Transforms applied.")
        return {'FINISHED'}

class HIFI_OT_copy_transform(bpy.types.Operator):
    bl_idname = "hifi.copy_transform"
    bl_label = "Copy Transform"
    bl_description = "Copy Location, Rotation, and Scale to Clipboard"
    @classmethod
    def poll(cls, context): return context.active_object is not None
    def execute(self, context):
        obj = context.active_object
        loc = obj.location
        rot = obj.rotation_euler
        scale = obj.scale
        
        copy_text = (
            f"Values For Code Walker: {loc.x:.6f}, {loc.y:.6f}, {loc.z:.6f}\n\n"
            "Location\n"
            f"X= {loc.x:.6f}\n"
            f"Y= {loc.y:.6f}\n"
            f"Z= {loc.z:.6f}\n"
            "Rotation\n"
            f"X= {math.degrees(rot.x):.6f}\n"
            f"Y= {math.degrees(rot.y):.6f}\n"
            f"Z= {math.degrees(rot.z):.6f}\n"
            "Scale\n"
            f"X= {scale.x:.6f}\n"
            f"Y= {scale.y:.6f}\n"
            f"Z= {scale.z:.6f}"
        )
        
        context.window_manager.clipboard = copy_text
        self.report({'INFO'}, "Transforms & Code Walker values copied to clipboard.")
        return {'FINISHED'}

class HIFI_OT_orphan_cleanup(bpy.types.Operator):
    bl_idname = "hifi.cleanup_orphans"
    bl_label = "Cleanup"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        hifi_orphan_cleanup()
        self.report({'INFO'}, "Orphaned data cleaned and report saved.")
        return {'FINISHED'}

class HIFI_OT_game_export(bpy.types.Operator):
    bl_idname = "hifi.game_export"
    bl_label = "Prepare for Export"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context): return context.active_object is not None
    def execute(self, context):
        obj = context.active_object
        try:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            obj.location = (0, 0, 0)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            self.report({'INFO'}, f"Prepared for export.")
        except Exception as e: pass
        return {'FINISHED'}
