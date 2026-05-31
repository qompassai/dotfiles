import bpy, math, mathutils
from .utils import PREVIEW_PREFIX, GEN_PREFIX

HIFI_ANIM_MEMORY = {
    "original_mesh_name": "", 
    "base_name": "",
    "arm_obj_name": "",
    "mesh_obj_name": "",
    "cd_obj_name": "",
    "action_name": "",
    "anim_frames": 240,
    "step1_done": False,
    "step2_done": False
}

def deferred_wipe():
    base_name = HIFI_ANIM_MEMORY.get("base_name", "")
    orig_name = HIFI_ANIM_MEMORY.get("original_mesh_name", "")
    
    if not base_name:
        for col in bpy.data.collections:
            if col.name.endswith("_export_room"):
                base_name = col.name.replace("_export_room", "")
                break
                
    if not base_name: 
        return None

    mesh_obj = None
    mesh_name_in_mem = HIFI_ANIM_MEMORY.get("mesh_obj_name", "")
    if mesh_name_in_mem:
        mesh_obj = bpy.data.objects.get(mesh_name_in_mem)
    if not mesh_obj:
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.name.startswith(base_name):
                mesh_obj = obj; break

    if mesh_obj:
        if mesh_obj.parent:
            matrixcopy = mesh_obj.matrix_world.copy()
            mesh_obj.parent = None
            mesh_obj.matrix_world = matrixcopy
        
        mod = mesh_obj.modifiers.get("hifi_armature")
        if mod: mesh_obj.modifiers.remove(mod)
        
        vg = mesh_obj.vertex_groups.get(f"{base_name}_rotation")
        if vg: mesh_obj.vertex_groups.remove(vg)
        
        if orig_name: 
            mesh_obj.name = orig_name
        else:
            mesh_obj.name = mesh_obj.name.replace("_mesh", "")
            
        main_col = bpy.context.scene.collection
        if mesh_obj.name not in main_col.objects:
            main_col.objects.link(mesh_obj)

    exp_col = bpy.data.collections.get(f"{base_name}_export_room")
    if exp_col:
        for obj in list(exp_col.objects):
            if obj != mesh_obj:
                if obj.type == 'ARMATURE':
                    ad = obj.data
                    bpy.data.objects.remove(obj, do_unlink=True)
                    if ad: bpy.data.armatures.remove(ad, do_unlink=True)
                else:
                    bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(exp_col)

    cd_name = HIFI_ANIM_MEMORY.get("cd_obj_name", "")
    if cd_name:
        cd_obj = bpy.data.objects.get(cd_name)
        if cd_obj:
            def delete_recursive(o):
                for c in list(o.children): delete_recursive(c)
                bpy.data.objects.remove(o, do_unlink=True)
            delete_recursive(cd_obj)
    
    for obj in list(bpy.data.objects):
        if obj.name.startswith(f"anim@{base_name}"):
            bpy.data.objects.remove(obj, do_unlink=True)

    for act in list(bpy.data.actions):
        if base_name in act.name.lower():
            bpy.data.actions.remove(act)
            
    try:
        scene = bpy.context.scene
        ytyps_list = getattr(scene, 'sollumz_ytyps', getattr(scene, 'ytyps', None))
        
        if ytyps_list is not None:
            for i in range(len(ytyps_list) - 1, -1, -1):
                if ytyps_list[i].name == base_name:
                    if hasattr(scene, 'sollumz_ytyp_index'):
                        scene.sollumz_ytyp_index = i
                    elif hasattr(scene, 'ytyp_index'):
                        scene.ytyp_index = i
                    try:
                        bpy.ops.sollumz.deleteytyp()
                    except: pass
    except: pass

    for key in HIFI_ANIM_MEMORY:
        if isinstance(HIFI_ANIM_MEMORY[key], bool): HIFI_ANIM_MEMORY[key] = False
        elif isinstance(HIFI_ANIM_MEMORY[key], str): HIFI_ANIM_MEMORY[key] = ""
    HIFI_ANIM_MEMORY["anim_frames"] = 240
    
    return None

def trigger_deep_wipe():
    bpy.app.timers.register(deferred_wipe, first_interval=0.1)

def run_sollumz_cmd(cmd_name):
    try:
        op = getattr(bpy.ops.sollumz, cmd_name)
        return op()
    except:
        return None

def force_parenting(child_obj, parent_obj):
    if child_obj and parent_obj:
        matrixcopy = child_obj.matrix_world.copy()
        child_obj.parent = parent_obj
        child_obj.matrix_world = matrixcopy

def select_for_outliner(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()

class HIFI_OT_anim_step1_rig(bpy.types.Operator):
    bl_idname = "hifi.anim_step1_rig"
    bl_label = "Step 1: Auto-Rig & Animate"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context): return context.active_object is not None and context.active_object.type == 'MESH'
        
    def execute(self, context):
        mesh_obj = context.active_object
        hp = context.scene.hifi_props
        
        original_mesh_name = mesh_obj.name
        HIFI_ANIM_MEMORY["original_mesh_name"] = original_mesh_name
        
        anim_frames = hp.anim_frames
        step_size = int(anim_frames / 8)
        
        context.scene.frame_start = 0
        context.scene.frame_end = anim_frames
        context.scene.frame_current = 0
        HIFI_ANIM_MEMORY["anim_frames"] = anim_frames
        
        raw_name = mesh_obj.name.replace(PREVIEW_PREFIX, "").replace(GEN_PREFIX, "").replace("_Mesh", "")
        base_name = "".join(c for c in raw_name if c.isalnum() or c in ['_', '-']).lower()
        if not base_name: base_name = "hifi_prop"
        HIFI_ANIM_MEMORY["base_name"] = base_name
        
        for act in list(bpy.data.actions):
            if base_name in act.name.lower(): bpy.data.actions.remove(act)
                
        if mesh_obj.parent and mesh_obj.parent.type == 'ARMATURE':
            old_arm = mesh_obj.parent
            matrixcopy = mesh_obj.matrix_world.copy()
            mesh_obj.parent = None
            mesh_obj.matrix_world = matrixcopy
            if base_name in old_arm.name.lower(): bpy.data.objects.remove(old_arm, do_unlink=True)
                
        for mod in list(mesh_obj.modifiers):
            if mod.type == 'ARMATURE' and ("hifi" in mod.name.lower() or base_name in mod.name.lower()):
                mesh_obj.modifiers.remove(mod)
                
        for vg in list(mesh_obj.vertex_groups):
            if base_name in vg.name.lower() or "rotation" in vg.name.lower() or "base" in vg.name.lower():
                mesh_obj.vertex_groups.remove(vg)
                
        is_sollumz = any("sollumz" in k.lower() for k in context.preferences.addons.keys()) and hp.use_sollumz
        
        try:
            col_name = f"{base_name}_export_room"
            if col_name not in bpy.data.collections:
                export_col = bpy.data.collections.new(col_name)
                context.scene.collection.children.link(export_col)
            else: 
                export_col = bpy.data.collections[col_name]
                
            for layer_col in context.view_layer.layer_collection.children:
                layer_col.exclude = (layer_col.name != col_name)
                
            for col in mesh_obj.users_collection: col.objects.unlink(mesh_obj)
            export_col.objects.link(mesh_obj)
            
            mesh_name = f"{base_name}_mesh"
            mesh_obj.name = mesh_name
            HIFI_ANIM_MEMORY["mesh_obj_name"] = mesh_name
            bpy.context.view_layer.update()
            
            select_for_outliner(mesh_obj)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            
            arm_data = bpy.data.armatures.new(f"{base_name}.skel")
            arm_name = base_name
            
            arm_obj = bpy.data.objects.new(arm_name, arm_data) 
            export_col.objects.link(arm_obj)
            
            actual_arm_name = arm_obj.name
            HIFI_ANIM_MEMORY["arm_obj_name"] = actual_arm_name
            arm_obj.location = mesh_obj.location.copy()
            
            if arm_obj.animation_data: arm_obj.animation_data_clear()
            bpy.context.view_layer.update()
            
            select_for_outliner(arm_obj)
            bpy.ops.object.mode_set(mode='EDIT')
            
            root_name = f"{base_name}_base"
            root_bone = arm_data.edit_bones.new(root_name)
            root_bone.head = (0, 0, 0); root_bone.tail = (0, 0, 0.1)
            
            rot_name = f"{base_name}_rotation"
            rot_bone = arm_data.edit_bones.new(rot_name)
            rot_bone.head = (0, 0, 0); rot_bone.tail = (0, 0.1, 0)
            rot_bone.parent = root_bone
            bpy.ops.object.mode_set(mode='OBJECT')
            
            force_parenting(mesh_obj, arm_obj)
            
            mod = mesh_obj.modifiers.new(name="hifi_armature", type='ARMATURE')
            mod.object = arm_obj
            vg = mesh_obj.vertex_groups.new(name=rot_name)
            verts = [v.index for v in mesh_obj.data.vertices]
            vg.add(verts, 1.0, 'REPLACE')
            
            select_for_outliner(arm_obj)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            arm_obj.data.edit_bones[rot_name].select = True
            arm_obj.data.edit_bones.active = arm_obj.data.edit_bones[rot_name]
            
            bpy.ops.object.mode_set(mode='POSE')
            pb = arm_obj.pose.bones[rot_name]
            db = arm_obj.data.bones[rot_name]
            
            try:
                db.bone_properties.flags_enum = {'RotX', 'RotY', 'RotZ', 'TransX', 'TransY', 'TransZ', 'ScaleX', 'ScaleY', 'ScaleZ'}
            except: pass
            
            pb.rotation_mode = 'QUATERNION'
            axis_idx = {'X':0, 'Y':1, 'Z':2}[hp.anim_axis]
            
            for i in range(9):
                frame = i * step_size
                angle_deg = i * 45
                angle = math.radians(angle_deg * (-1 if hp.anim_reverse else 1))
                
                e = [0, 0, 0]
                e[axis_idx] = angle
                pb.rotation_quaternion = mathutils.Euler(e, 'XYZ').to_quaternion()
                pb.location = (0, 0, 0)
                pb.scale = (1, 1, 1)
                
                pb.keyframe_insert(data_path="location", frame=frame)
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                pb.keyframe_insert(data_path="scale", frame=frame)
                
            try:
                if arm_obj.animation_data and arm_obj.animation_data.action:
                    act = arm_obj.animation_data.action
                    act.name = f"{base_name}_action"
                    HIFI_ANIM_MEMORY["action_name"] = act.name
            except: pass

            try:
                target_area = next((a for a in bpy.context.window.screen.areas if a.type in ['VIEW_3D', 'TEXT_EDITOR']), None)
                if target_area:
                    old_type = target_area.type
                    target_area.type = 'DOPESHEET_EDITOR'
                    with bpy.context.temp_override(area=target_area):
                        bpy.ops.action.select_all(action='SELECT')
                        for _ in range(5):
                            bpy.ops.action.interpolation_type(type='LINEAR')
                            bpy.ops.action.handle_type(type='VECTOR')
                    target_area.type = old_type
            except: pass
            
            context.scene.frame_set(0)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.update()
            
            if is_sollumz:
                has_sollumz_mat = False
                for mat in mesh_obj.data.materials:
                    if mat and getattr(mat, 'sollum_type', '') == 'sollumz_material':
                        has_sollumz_mat = True; break
                
                if not has_sollumz_mat:
                    select_for_outliner(mesh_obj)
                    try:
                        if "WinMan" in bpy.data.window_managers: bpy.data.window_managers["WinMan"].sz_shader_material_index = 1
                        else: bpy.context.window_manager.sz_shader_material_index = 1
                    except: pass
                    run_sollumz_cmd('createshadermaterial')
                
                select_for_outliner(arm_obj)
                res = run_sollumz_cmd('converttodrawable')
                if res == {'CANCELLED'} or res is None: arm_obj.sollum_type = 'sollumz_drawable'
                arm_obj.name = arm_name 
                bpy.context.view_layer.update()
                
                select_for_outliner(mesh_obj)
                res_mesh = run_sollumz_cmd('converttodrawablemodel')
                if res_mesh == {'CANCELLED'} or res_mesh is None: mesh_obj.sollum_type = 'sollumz_drawable_model'
                mesh_obj.name = mesh_name
                bpy.context.view_layer.update()
            
            HIFI_ANIM_MEMORY["step1_done"] = True
            self.report({'INFO'}, "Step 1 complete.")
            return {'FINISHED'}
        except:
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except: pass
            self.report({'ERROR'}, "Step 1 failed.")
            return {'CANCELLED'}

class HIFI_OT_anim_step2_clipdict(bpy.types.Operator):
    bl_idname = "hifi.anim_step2_clipdict"
    bl_label = "Step 2: Create Clip Dictionary"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context): return context.scene.hifi_props.use_sollumz
        
    def execute(self, context):
        if not HIFI_ANIM_MEMORY["step1_done"]:
            self.report({'WARNING'}, "Please run Step 1 first.")
            return {'CANCELLED'}
            
        base_name = HIFI_ANIM_MEMORY["base_name"]
        dict_name = f"anim@{base_name}"
        
        arm_name = HIFI_ANIM_MEMORY["arm_obj_name"]
        act_name = HIFI_ANIM_MEMORY.get("action_name", f"{base_name}_action")
        
        hp = context.scene.hifi_props
        anim_frames = hp.anim_frames 
        anim_duration = float(anim_frames) / 30.0
        
        actual_skeleton = None
        mesh_name = HIFI_ANIM_MEMORY["mesh_obj_name"]
        mesh_obj = bpy.data.objects.get(mesh_name)
        
        if mesh_obj and mesh_obj.parent and mesh_obj.parent.type == 'ARMATURE':
            actual_skeleton = mesh_obj.parent
        if not actual_skeleton:
            actual_skeleton = bpy.data.objects.get(arm_name)
        if not actual_skeleton:
            exp_col = bpy.data.collections.get(f"{base_name}_export_room")
            if exp_col:
                for obj in exp_col.objects:
                    if obj.type == 'ARMATURE':
                        actual_skeleton = obj; break
                        
        if not actual_skeleton:
            self.report({'ERROR'}, "Skeleton missing.")
            return {'CANCELLED'}
            
        old_cd = bpy.data.objects.get(dict_name)
        if old_cd:
            def delete_recursive(obj):
                for child in list(obj.children): delete_recursive(child)
                bpy.data.objects.remove(obj, do_unlink=True)
            delete_recursive(old_cd)
        
        try:
            context.scene.sollumz_animations_target_id_type = 'ARMATURE'
            context.scene.sollumz_animations_target_id = actual_skeleton
        except: pass
        
        export_col = bpy.data.collections.get(f"{base_name}_export_room")
        main_col = context.scene.collection
        
        try:
            old_objs = set(bpy.data.objects)
            select_for_outliner(actual_skeleton)
            
            run_sollumz_cmd('create_clip_dictionary')
            bpy.context.view_layer.update()
            
            new_objs = list(set(bpy.data.objects) - old_objs)
            cd_obj = next((o for o in new_objs if getattr(o, 'sollum_type', '') == 'sollumz_clip_dictionary'), None)

            if cd_obj:
                cd_obj.name = dict_name
                HIFI_ANIM_MEMORY["cd_obj_name"] = cd_obj.name
                
                if export_col and cd_obj.name in export_col.objects: export_col.objects.unlink(cd_obj)
                if cd_obj.name not in main_col.objects: main_col.objects.link(cd_obj)
                
                anim_empty, clip_empty = None, None
                for child in cd_obj.children:
                    if export_col and child.name in export_col.objects: export_col.objects.unlink(child)
                    if child.name not in main_col.objects: main_col.objects.link(child)
                        
                    if "animation" in child.name.lower(): anim_empty = child
                    if "clip" in child.name.lower() and "dict" not in child.name.lower(): clip_empty = child

                anim_obj = None
                if anim_empty:
                    old_objs = set(bpy.data.objects)
                    select_for_outliner(anim_empty)
                    
                    run_sollumz_cmd('create_animation')
                    bpy.context.view_layer.update()
                    
                    new_anims = list(set(bpy.data.objects) - old_objs)
                    if new_anims:
                        anim_obj = new_anims[0]
                        anim_obj.name = base_name 
                        force_parenting(anim_obj, anim_empty) 
                        
                        try: anim_obj.animation_properties.hash = base_name
                        except: pass
                        try: anim_obj.animation_properties.name = base_name
                        except: pass
                        
                        try: 
                            anim_obj.animation_properties.target_id = actual_skeleton.data
                        except:
                            try: anim_obj.animation_properties.target_id = actual_skeleton
                            except: pass
                            
                        try: anim_obj.animation_properties.start_frame = 0
                        except: pass
                        try: anim_obj.animation_properties.end_frame = anim_frames
                        except: pass
                        
                        try:
                            act = bpy.data.actions.get(act_name)
                            if act: 
                                anim_obj.animation_properties.action = act
                        except: pass
                        
                clip_obj = None
                if clip_empty:
                    old_objs = set(bpy.data.objects)
                    select_for_outliner(clip_empty)
                    
                    run_sollumz_cmd('create_clip')
                    bpy.context.view_layer.update()
                    
                    new_clips = list(set(bpy.data.objects) - old_objs)
                    if new_clips:
                        clip_obj = new_clips[0]
                        clip_obj.name = base_name
                        force_parenting(clip_obj, clip_empty) 
                            
                        try:
                            clip_obj.clip_properties.hash = base_name 
                            clip_obj.clip_properties.name = f"{base_name}.clip"
                            clip_obj.clip_properties.duration = anim_duration
                            clip_obj.clip_properties.start_frame = 0
                            clip_obj.clip_properties.end_frame = anim_frames
                        except: pass
                        
                        if anim_obj:
                            select_for_outliner(clip_obj)
                            run_sollumz_cmd('clip_new_animation')
                            try: clip_obj.clip_properties.animations[-1].animation = anim_obj
                            except: pass

            select_for_outliner(actual_skeleton)
            HIFI_ANIM_MEMORY["step2_done"] = True
            self.report({'INFO'}, "Step 2: Clip Dictionary generated successfully.")
            return {'FINISHED'}
        except:
            self.report({'ERROR'}, "Step 2 Failed.")
            return {'CANCELLED'}

class HIFI_OT_anim_step3_ytyp(bpy.types.Operator):
    bl_idname = "hifi.anim_step3_ytyp"
    bl_label = "Step 3: Create YTYP & Archetype"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context): return context.scene.hifi_props.use_sollumz
        
    def execute(self, context):
        if not HIFI_ANIM_MEMORY["step2_done"]:
            self.report({'WARNING'}, "Please run Step 2 before creating a YTYP.")
            return {'CANCELLED'}
            
        base_name = HIFI_ANIM_MEMORY["base_name"]
        dict_name = f"anim@{base_name}"
        
        arm_name = HIFI_ANIM_MEMORY["arm_obj_name"]
        mesh_name = HIFI_ANIM_MEMORY["mesh_obj_name"]
        mesh_obj = bpy.data.objects.get(mesh_name)
        
        actual_skeleton = None
        if mesh_obj and mesh_obj.parent and mesh_obj.parent.type == 'ARMATURE':
            actual_skeleton = mesh_obj.parent
        if not actual_skeleton: actual_skeleton = bpy.data.objects.get(arm_name)
        
        try:
            ytyps_list = getattr(context.scene, 'sollumz_ytyps', getattr(context.scene, 'ytyps', []))
            old_ytyp_count = len(ytyps_list)
            
            run_sollumz_cmd('createytyp')
            bpy.context.view_layer.update()
            
            ytyps_list = getattr(context.scene, 'sollumz_ytyps', getattr(context.scene, 'ytyps', []))
            if len(ytyps_list) > old_ytyp_count:
                ytyp_idx = len(ytyps_list) - 1
                ytyp = ytyps_list[ytyp_idx]
                ytyp.name = base_name
                
                if hasattr(context.scene, 'sollumz_ytyp_index'): context.scene.sollumz_ytyp_index = ytyp_idx
                elif hasattr(context.scene, 'ytyp_index'): context.scene.ytyp_index = ytyp_idx
                
                try: context.scene.create_archetype_type = 'sollumz_archetype_base'
                except: pass
                
                if actual_skeleton: select_for_outliner(actual_skeleton)
                
                old_arch_count = len(ytyp.archetypes) if hasattr(ytyp, 'archetypes') else 0
                run_sollumz_cmd('createarchetypefromselected')
                bpy.context.view_layer.update()
                
                if hasattr(ytyp, 'archetypes') and len(ytyp.archetypes) > old_arch_count:
                    arch_idx = len(ytyp.archetypes) - 1
                    try: ytyp.archetype_index = arch_idx
                    except: pass
                    
                    arch = ytyp.archetypes[arch_idx]
                    arch.name = base_name
                    arch.asset_name = base_name
                    arch.type = 'sollumz_archetype_base'
                    arch.clip_dictionary = dict_name 
                    
                    if hasattr(arch, 'asset') and actual_skeleton:
                        arch.asset = actual_skeleton
                        
                    try:
                        root_ytyp_list = getattr(bpy.context.scene, 'sollumz_ytyps', getattr(bpy.context.scene, 'ytyps', []))
                        target_ytyp = root_ytyp_list[ytyp_idx]
                        target_ytyp.archetypes_access_flags_flag10_ = True
                        target_ytyp.archetypes_access_flags_flag20_ = True
                    except: pass
            
            self.report({'INFO'}, "Step 3: Asset successfully prepared for export.")
            return {'FINISHED'}
        except:
            self.report({'ERROR'}, "Step 3 Failed.")
            return {'CANCELLED'}
