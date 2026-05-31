import bpy
import math
import mathutils
import re
import os
from pathlib import Path

# ========================
# CORE FUNCTIONS
# ========================
SECTION_NAMES = {
    1: "Sculpting",
    2: "Check HP mesh",
    3: "Retopology",
    4: "Check LP mesh",
    5: "Texturing",
}
ITEM_NAMES = {
    1: ["Blocking", "Large shapes", "Medium shapes", "Small details"],
    2: ["Holes", "Gaps", "Splines", "Shading"],
    3: ["Retopology"],
    4: ["Holes", "Gaps", "Splines", "Shading"],
    5: ["Unwrap", "Bake", "Texturing"],
}
TOTAL_SECTIONS = 5

def count_model_roots():
    roots = set()
    for col in bpy.data.collections:
        if col.name.endswith("_High"):
            root_col = bpy.data.collections.get(col.name[:-5])
            if root_col and has_high_low_children(root_col):
                roots.add(root_col.name)
        elif col.name.endswith("_Low"):
            root_col = bpy.data.collections.get(col.name[:-4])
            if root_col and has_high_low_children(root_col):
                roots.add(root_col.name)
    return roots

def find_model_root_from_context():
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        for col in obj.users_collection:
            root = climb_to_model_root(col)
            if root:
                return root
    try:
        alc = bpy.context.view_layer.active_layer_collection
        if alc:
            col = bpy.data.collections.get(alc.name)
            if col:
                if has_high_low_children(col):
                    return col
                root = climb_to_model_root(col)
                if root:
                    return root
    except Exception:
        pass

    roots = count_model_roots()
    if len(roots) == 1:
        return bpy.data.collections.get(next(iter(roots)))

    return None

def climb_to_model_root(col):
    if has_high_low_children(col):
        return col
    current = col
    visited = set()
    for _ in range(20):
        if current.name in visited:
            break
        visited.add(current.name)
        parent = None
        for candidate in bpy.data.collections:
            if current.name in [c.name for c in candidate.children]:
                parent = candidate
                break
        if parent is None:
            break
        if has_high_low_children(parent):
            return parent
        current = parent
    return None

def has_high_low_children(col):
    name = col.name
    high_name = f"{name}_High"
    low_name = f"{name}_Low"
    has_high = any(c.name == high_name for c in col.children)
    has_low = any(c.name == low_name for c in col.children)
    return has_high and has_low

def get_item_count(sec):
    return len(ITEM_NAMES.get(sec, []))

def is_section_complete(scene, sec):
    count = get_item_count(sec)
    return all(getattr(scene, f"cp_section_{sec}_item_{i}", False) for i in range(1, count + 1))

def is_section_unlocked(scene, sec):
    for s in range(1, sec):
        if not is_section_complete(scene, s):
            return False
    return True

def is_item_unlocked(scene, sec, item):
    if not is_section_unlocked(scene, sec):
        return False
    for i in range(1, item):
        if not getattr(scene, f"cp_section_{sec}_item_{i}", False):
            return False
    return True

def get_unique_collection_name(base_name):
    if base_name not in bpy.data.collections:
        return base_name
    counter = 2
    while f"{base_name} {counter}" in bpy.data.collections:
        counter += 1
    return f"{base_name} {counter}"

def direction_to_euler(direction):
    vec = mathutils.Vector(direction)
    vec.normalize()
    quat = vec.to_track_quat('-Z', 'Y')
    return quat.to_euler()

def apply_modifiers_only(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:
            pass
    obj.select_set(False)

def apply_transforms_only(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)

def normalize_name(name, target_suffix, patterns):
    name_clean = re.sub(r'.\d{3}$', '', name)
    for pat in patterns:
        if name_clean.lower().endswith(pat.lower()):
            name_clean = name_clean[:-len(pat)]
            break
    while name_clean.endswith(('_', '.')):
        name_clean = name_clean[:-1]
    return name_clean + target_suffix

def find_collections_by_suffix(suffix):
    return [col for col in bpy.data.collections if col.name.endswith(suffix)]

def get_model_name_from_collection(col_name):
    if col_name.endswith("_High"):
        return col_name[:-5]
    elif col_name.endswith("_Low"):
        return col_name[:-4]
    return None

# ========================
# OPERATORS
# ========================
class CP_OT_setup_collections(bpy.types.Operator):
    bl_idname = "cp.setup_collections"
    bl_label = "Collection Setup"
    bl_description = "Create Model, High and Low collections with unique names"
    def execute(self, context):
        base_name = context.scene.cp_model_name.strip()
        if not base_name:
            base_name = "Model"
        model_name = get_unique_collection_name(base_name)
        high_name = f"{model_name}_High"
        low_name = f"{model_name}_Low"

        model_col = bpy.data.collections.new(model_name)
        high_col = bpy.data.collections.new(high_name)
        low_col = bpy.data.collections.new(low_name)
        high_col.color_tag = 'COLOR_01'
        low_col.color_tag = 'COLOR_05'

        model_col.children.link(high_col)
        model_col.children.link(low_col)
        context.scene.collection.children.link(model_col)

        lc = context.view_layer.layer_collection

        def find_layer_collection(col_name, layer_col):
            for child in layer_col.children:
                if child.name == col_name:
                    return child
                result = find_layer_collection(col_name, child)
                if result:
                    return result
            return None

        high_lc = find_layer_collection(high_name, lc)
        if high_lc:
            context.view_layer.active_layer_collection = high_lc

        context.scene.cp_model_name = ""
        self.report({'INFO'}, f"Created: {model_name}, {high_name}, {low_name}")
        return {'FINISHED'}

class CP_OT_prepare_hp(bpy.types.Operator):
    bl_idname = "cp.prepare_hp"
    bl_label = 'Prepare HP'
    bl_description = "Normalize mesh names to '_high' and apply all modifiers"
    def execute(self, context):
        high_collections = find_collections_by_suffix("_High")
        if not high_collections:
            self.report({'WARNING'}, "No collections ending with '_High' found")
            return {'CANCELLED'}

        total_normalized = 0
        high_patterns = ["_high", "_hp", ".high", ".hp"]

        for col in high_collections:
            model_name = get_model_name_from_collection(col.name)
            if not model_name:
                continue
            meshes_high = [obj for obj in col.objects if obj.type == 'MESH']
            if meshes_high:
                all_correct = all(obj.name.lower().endswith("_high") for obj in meshes_high)
                if not all_correct:
                    for obj in meshes_high:
                        obj.name = normalize_name(obj.name, "_high", high_patterns)
                    total_normalized += len(meshes_high)
                for obj in meshes_high:
                    apply_modifiers_only(obj)

        if total_normalized == 0:
            self.report({'INFO'}, "All _High objects already use '_high' suffix")
        else:
            self.report({'INFO'}, f"Normalized {total_normalized} object(s) to '_high'")
        return {'FINISHED'}

class CP_OT_prepare_lp(bpy.types.Operator):
    bl_idname = "cp.prepare_lp"
    bl_label = 'Prepare LP'
    bl_description = "Normalize mesh names to '_low' and apply modifiers"
    def execute(self, context):
        low_collections = find_collections_by_suffix("_Low")
        if not low_collections:
            self.report({'WARNING'}, "No collections ending with '_Low' found")
            return {'CANCELLED'}

        total_normalized = 0
        low_patterns = ["_low", ".low", "_lp", ".lp", "_high", ".high", "_hp", ".hp"]

        for col in low_collections:
            model_name = get_model_name_from_collection(col.name)
            if not model_name:
                continue
            meshes = [obj for obj in col.objects if obj.type == 'MESH']
            if not meshes:
                continue

            all_correct = all(obj.name.lower().endswith("_low") for obj in meshes)
            if not all_correct:
                for obj in meshes:
                    obj.name = normalize_name(obj.name, "_low", low_patterns)
                total_normalized += len(meshes)

            for obj in meshes:
                apply_modifiers_only(obj)

            root_col = next((p for p in bpy.data.collections if col.name in [c.name for c in p.children]), None)
            if root_col:
                for obj in root_col.objects:
                    if obj.type == 'MESH':
                        apply_modifiers_only(obj)

        if total_normalized == 0:
            self.report({'INFO'}, "All _Low objects already use '_low' suffix")
        else:
            self.report({'INFO'}, f"Normalized {total_normalized} object(s) to '_low'")
        return {'FINISHED'}

class CP_OT_validate_pairs(bpy.types.Operator):
    bl_idname = "cp.validate_pairs"
    bl_label = 'Validate Pairs'
    bl_description = "Check if each _high object has a corresponding _low object"
    def execute(self, context):
        root = find_model_root_from_context()
        if not root:
            self.report({'WARNING'}, "Active collection is not part of a valid model structure")
            return {'CANCELLED'}

        model_name = root.name
        high_col_name = f"{model_name}_High"
        low_col_name = f"{model_name}_Low"

        high_objs = {}
        low_objs = {}

        if high_col_name in bpy.data.collections:
            for obj in bpy.data.collections[high_col_name].objects:
                if obj.type == 'MESH':
                    base = re.sub(r'_high$', '', obj.name, flags=re.IGNORECASE)
                    high_objs.setdefault(base, []).append(obj)

        if low_col_name in bpy.data.collections:
            for obj in bpy.data.collections[low_col_name].objects:
                if obj.type == 'MESH':
                    base = re.sub(r'_low$', '', obj.name, flags=re.IGNORECASE)
                    low_objs.setdefault(base, []).append(obj)

        duplicate_objects = []
        duplicate_bases = set()

        for base, objs in high_objs.items():
            if len(objs) > 1:
                duplicate_objects.extend(objs)
                duplicate_bases.add(f"High: {base}")
        for base, objs in low_objs.items():
            if len(objs) > 1:
                duplicate_objects.extend(objs)
                duplicate_bases.add(f"Low: {base}")

        missing_in_low = set(high_objs.keys()) - set(low_objs.keys())
        missing_in_high = set(low_objs.keys()) - set(high_objs.keys())

        bpy.ops.object.select_all(action='DESELECT')
        isolated_objects = []

        for obj in duplicate_objects:
            obj.select_set(True)
            isolated_objects.append(obj)
        for base in missing_in_low:
            for obj in high_objs.get(base, []):
                obj.select_set(True)
                isolated_objects.append(obj)
        for base in missing_in_high:
            for obj in low_objs.get(base, []):
                obj.select_set(True)
                isolated_objects.append(obj)

        messages = []
        if duplicate_bases:
            messages.append(f"Duplicate base names: {', '.join(sorted(duplicate_bases))}")
        if missing_in_low:
            messages.append(f"Missing in Low: {', '.join(missing_in_low)}")
        if missing_in_high:
            messages.append(f"Missing in High: {', '.join(missing_in_high)}")

        if messages:
            self.report({'WARNING'}, "; ".join(messages))
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    with context.temp_override(area=area):
                        if isolated_objects:
                            bpy.ops.view3d.localview(frame_selected=False)
                    break
        else:
            self.report({'INFO'}, "All pairs match and no duplicates found!")
        
        return {'FINISHED'}

class CP_OT_check_lp_mesh(bpy.types.Operator):
    bl_idname = "cp.check_lp_mesh"
    bl_label = 'Check LP'
    bl_description = "Check mesh issues in Low and root model collections"
    def execute(self, context):
        import bmesh
        root = find_model_root_from_context()
        if not root:
            self.report({'WARNING'}, "Active collection is not part of a valid model structure")
            return {'CANCELLED'}

        model_name = root.name
        low_col = bpy.data.collections.get(f"{model_name}_Low")
        objects_to_check = []

        for obj in root.objects:
            if obj.type == 'MESH':
                objects_to_check.append(obj)
        if low_col:
            for obj in low_col.objects:
                if obj.type == 'MESH':
                    objects_to_check.append(obj)

        if not objects_to_check:
            self.report({'INFO'}, "No mesh objects to check in Low or root collection")
            return {'FINISHED'}

        bad_objects = []
        for obj in objects_to_check:
            me = obj.data
            to_remove = [vg for vg in obj.vertex_groups if vg.name.startswith("CHECK_")]
            for vg in to_remove:
                obj.vertex_groups.remove(vg)

            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()

            issues_found = False

            zero_faces = [f for f in bm.faces if f.calc_area() <= 1e-8]
            if zero_faces:
                vg = obj.vertex_groups.new(name="CHECK_ZeroFaces")
                vg.add([v.index for f in zero_faces for v in f.verts], 1.0, 'REPLACE')
                issues_found = True

            zero_edges = [e for e in bm.edges if e.calc_length() <= 1e-8]
            if zero_edges:
                vg = obj.vertex_groups.new(name="CHECK_ZeroEdges")
                vg.add([v.index for e in zero_edges for v in e.verts], 1.0, 'REPLACE')
                issues_found = True

            loose_verts = [v for v in bm.verts if len(v.link_faces) == 0 and len(v.link_edges) == 0]
            if loose_verts:
                vg = obj.vertex_groups.new(name="CHECK_LooseVerts")
                vg.add([v.index for v in loose_verts], 1.0, 'REPLACE')
                issues_found = True

            boundary_edges = [e for e in bm.edges if len(e.link_faces) == 1]
            if boundary_edges:
                vg = obj.vertex_groups.new(name="CHECK_Holes")
                vg.add([v.index for e in boundary_edges for v in e.verts], 1.0, 'REPLACE')
                issues_found = True

            nonmanifold_edges = [e for e in bm.edges if len(e.link_faces) > 2 or len(e.link_faces) == 0]
            if nonmanifold_edges:
                vg = obj.vertex_groups.new(name="CHECK_NonManifold")
                vg.add([v.index for e in nonmanifold_edges for v in e.verts], 1.0, 'REPLACE')
                issues_found = True

            bm.free()
            if issues_found:
                bad_objects.append(obj)

        if bad_objects:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in bad_objects:
                obj.select_set(True)
            context.view_layer.objects.active = bad_objects[0] if bad_objects else None

            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    with context.temp_override(area=area):
                        bpy.ops.view3d.localview(frame_selected=False)
                    break
            self.report({'WARNING'}, f"Found issues in {len(bad_objects)} object(s). See CHECK_* vertex groups.")
        else:
            self.report({'INFO'}, "No mesh issues found in Low/root collections")
        return {'FINISHED'}

def find_root_for_visibility(context):

    obj = context.active_object
    if obj and obj.type == 'MESH':
        for col in obj.users_collection:
            root = climb_to_model_root(col)
            if root:
                return root

    for obj in context.selected_objects:
        if obj.type == 'MESH':
            for col in obj.users_collection:
                root = climb_to_model_root(col)
                if root:
                    return root

    alc = context.view_layer.active_layer_collection
    if alc:
        col = bpy.data.collections.get(alc.name)
        if col:
            if has_high_low_children(col):
                return col
            root = climb_to_model_root(col)
            if root:
                return root
    return None

def show_all_addon_collections():
    for col in bpy.data.collections:
        if col.name.endswith("_High") or col.name.endswith("_Low"):
            col.hide_viewport = False

class CP_OT_toggle_high_visibility(bpy.types.Operator):
    bl_idname = "cp.toggle_high_visibility"
    bl_label = "Toggle High Visibility"
    def execute(self, context):
        root = find_root_for_visibility(context)
        if not root:
            show_all_addon_collections()
            return {'FINISHED'}
        col = bpy.data.collections.get(f"{root.name}_High")
        if col:
            col.hide_viewport = not col.hide_viewport
        return {'FINISHED'}

class CP_OT_toggle_low_visibility(bpy.types.Operator):
    bl_idname = "cp.toggle_low_visibility"
    bl_label = "Toggle Low Visibility"
    def execute(self, context):
        root = find_root_for_visibility(context)
        if not root:
            show_all_addon_collections()
            return {'FINISHED'}
        col = bpy.data.collections.get(f"{root.name}_Low")
        if col:
            col.hide_viewport = not col.hide_viewport
        return {'FINISHED'}

def get_high_visibility_label(context):
    root = find_root_for_visibility(context)
    if not root:
        return "Show HP"
    col = bpy.data.collections.get(f"{root.name}_High")
    return "Show HP" if col and col.hide_viewport else "Hide HP"

def get_low_visibility_label(context):
    root = find_root_for_visibility(context)
    if not root:
        return "Show LP"
    col = bpy.data.collections.get(f"{root.name}_Low")
    return "Show LP" if col and col.hide_viewport else "Hide LP"

class CP_OT_clean_scene(bpy.types.Operator):
    bl_idname = "cp.clean_scene"
    bl_label = 'Clean scene'
    bl_description = "Purge unused data"
    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for vg in [vg for vg in obj.vertex_groups if vg.name.startswith("CHECK_")]:
                    obj.vertex_groups.remove(vg)
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        self.report({'INFO'}, "Unused data purged and CHECK_* vertex groups removed")
        return {'FINISHED'}

class CP_OT_export_bake(bpy.types.Operator):
    bl_idname = "cp.export_bake"
    bl_label = 'Export bake'
    def execute(self, context):
        root_col = find_model_root_from_context()
        if not root_col:
            self.report({'ERROR'}, "Select an object or collection belonging to a character hierarchy first.")
            return {'CANCELLED'}
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save .blend file first!")
            return {'CANCELLED'}

        model_name = root_col.name
        bake_dir = os.path.join(os.path.dirname(bpy.data.filepath), "Bake")
        os.makedirs(bake_dir, exist_ok=True)

        high_col = low_col = None
        for col in root_col.children:
            if col.name == f"{model_name}_High": high_col = col
            elif col.name == f"{model_name}_Low": low_col = col

        if not high_col or not low_col:
            self.report({'ERROR'}, "Missing _High or _Low subcollection")
            return {'CANCELLED'}

        mat_high = bpy.data.materials.get(f"{model_name}_high") or bpy.data.materials.new(name=f"{model_name}_high")
        mat_low = bpy.data.materials.get(model_name) or bpy.data.materials.new(name=model_name)

        for obj in high_col.objects:
            if obj.type == 'MESH':
                apply_transforms_only(obj)
                if obj.data.materials: obj.data.materials[0] = mat_high
                else: obj.data.materials.append(mat_high)

        for obj in low_col.objects:
            if obj.type == 'MESH':
                apply_transforms_only(obj)
                if obj.data.materials: obj.data.materials[0] = mat_low
                else: obj.data.materials.append(mat_low)

        for col, name in [(high_col, f"{model_name}_high.fbx"), (low_col, f"{model_name}_low.fbx")]:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in col.objects:
                if obj.type == 'MESH': obj.select_set(True)
            if context.selected_objects:
                bpy.ops.export_scene.fbx(filepath=os.path.join(bake_dir, name), use_selection=True, bake_anim=False)

        bpy.ops.object.select_all(action='DESELECT')
        self.report({'INFO'}, "Export done")
        return {'FINISHED'}

class CP_OT_export_paint(bpy.types.Operator):
    bl_idname = "cp.export_paint"
    bl_label = 'Export paint'
    def execute(self, context):
        root_col = find_model_root_from_context()
        if not root_col:
            self.report({'ERROR'}, "Select an object or collection belonging to a character hierarchy first.")
            return {'CANCELLED'}
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save .blend file first!")
            return {'CANCELLED'}
        model_name = root_col.name
        mat_high = bpy.data.materials.get(f"{model_name}_high") or bpy.data.materials.new(name=f"{model_name}_high")
        mat_low = bpy.data.materials.get(model_name) or bpy.data.materials.new(name=model_name)

        high_col = bpy.data.collections.get(f"{model_name}_High")
        if high_col:
            for obj in high_col.objects:
                if obj.type == 'MESH':
                    apply_transforms_only(obj)
                    if obj.data.materials: obj.data.materials[0] = mat_high
                    else: obj.data.materials.append(mat_high)

        low_col = bpy.data.collections.get(f"{model_name}_Low")
        if low_col:
            for obj in low_col.objects:
                if obj.type == 'MESH':
                    apply_transforms_only(obj)
                    if obj.data.materials: obj.data.materials[0] = mat_low
                    else: obj.data.materials.append(mat_low)

        for obj in root_col.objects:
            if obj.type == 'MESH':
                apply_transforms_only(obj)
                if obj.data.materials: obj.data.materials[0] = mat_low
                else: obj.data.materials.append(mat_low)

        paint_dir = os.path.join(os.path.dirname(bpy.data.filepath), "Paint")
        os.makedirs(paint_dir, exist_ok=True)
        paint_path = os.path.join(paint_dir, f"{model_name}_paint.fbx")

        objects_to_export = []
        def collect_objects(col):
            for obj in col.objects:
                if obj.type == 'MESH': objects_to_export.append(obj)
            for child in col.children:
                if not child.name.endswith("_High"):
                    collect_objects(child)
        collect_objects(root_col)

        if not objects_to_export:
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export: obj.select_set(True)
        bpy.ops.export_scene.fbx(filepath=paint_path, use_selection=True, bake_anim=False)
        bpy.ops.object.select_all(action='DESELECT')
        self.report({'INFO'}, "Export done")
        return {'FINISHED'}

class CP_OT_final_export(bpy.types.Operator):
    bl_idname = "cp.final_export"
    bl_label = "Final export"
    def execute(self, context):
        scene = context.scene
        objects_to_export = []
        model_name = None
        root_col = find_model_root_from_context()

        if not root_col:
            self.report({'ERROR'}, "Select an object or collection belonging to a character hierarchy first.")
            return {'CANCELLED'}

        model_name = root_col.name
        low_col = bpy.data.collections.get(f"{model_name}_Low")
        def collect_from_collections(cols):
            meshes = []
            for col in cols:
                for obj in col.objects:
                    if obj.type == 'MESH' and not obj.hide_viewport: meshes.append(obj)
                for child in col.children:
                    if not child.name.endswith("_High"): meshes.extend(collect_from_collections([child]))
            return meshes
        collections_to_scan = [root_col] + ([low_col] if low_col else [])
        objects_to_export = collect_from_collections(collections_to_scan)
        mat = bpy.data.materials.get(model_name) or bpy.data.materials.new(name=model_name)

        if not objects_to_export:
            self.report({'ERROR'}, "No mesh objects found in the selected character collection.")
            return {'CANCELLED'}

        for obj in objects_to_export:
            if obj.data.materials: obj.data.materials[0] = mat
            else: obj.data.materials.append(mat)
            apply_transforms_only(obj)

        export_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else bpy.path.abspath("//")
        if not export_dir or export_dir == "//":
            self.report({'ERROR'}, "Save .blend file first!")
            return {'CANCELLED'}

        ext = {'FBX': '.fbx', 'OBJ': '.obj', 'GLB': '.glb'}.get(scene.cp_export_format, '.fbx')
        filepath = os.path.join(export_dir, model_name + ext)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export: obj.select_set(True)
        if objects_to_export: context.view_layer.objects.active = objects_to_export[0]

        try:
            if scene.cp_export_format == 'FBX': bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, bake_anim=False)
            elif scene.cp_export_format == 'OBJ': bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
            elif scene.cp_export_format == 'GLB': bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLB', use_selection=True)
            self.report({'INFO'}, f"Exported: {os.path.basename(filepath)}")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

class CP_OT_model_sheet(bpy.types.Operator):
    bl_idname = "cp.model_sheet"
    bl_label = "Model sheet"
    def execute(self, context):
        has_video_editing = any(ws.name == "Video Editing" for ws in bpy.data.workspaces)
        if not has_video_editing:
            self.report({'WARNING'}, "Video Editing workspace not found. Create it manually.")

        context.scene.name = "Character"
        char_scene = context.scene

        model_sheet_name = "Model Sheet"
        if model_sheet_name in bpy.data.scenes:
            bpy.data.scenes.remove(bpy.data.scenes[model_sheet_name])
        model_sheet_scene = bpy.data.scenes.new(model_sheet_name)


        model_sheet_scene.frame_start = 0
        model_sheet_scene.frame_end = 0

        prefs = context.preferences.addons.get(__package__, {}).preferences
        model_sheet_scene.render.film_transparent = getattr(prefs, 'model_sheet_use_transparent_bg', False)

        char_scene.render.resolution_x = 1000
        char_scene.render.resolution_y = 1000

        cam_col = bpy.data.collections.get("Cameras") or bpy.data.collections.new("Cameras")
        if cam_col not in char_scene.collection.children.values():
            char_scene.collection.children.link(cam_col)

        cam_data = [
            ("3/4", 'PERSP', (-1.6, -2.5, 1.9), (0, 0, 1.0)),
            ("Front", 'ORTHO', (0, -2.0, 1.0), (0, 0, 1.0)),
            ("Back", 'ORTHO', (0, 2.0, 1.0), (0, 0, 1.0)),
            ("Side", 'ORTHO', (2.0, 0, 1.0), (0, 0, 1.0)),
            ("Top", 'ORTHO', (0, 0, 3.0), (0, 0, 0)),
        ]

        cameras = []
        for name, proj, loc, target in cam_data:
            cam_name = f"Cam_{name}"
            if cam_name in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[cam_name], do_unlink=True)

            cam_data_obj = bpy.data.cameras.new(name=cam_name)
            cam_data_obj.type = proj
            if proj == 'ORTHO': cam_data_obj.ortho_scale = 2.5

            cam_obj = bpy.data.objects.new(cam_name, cam_data_obj)
            cam_col.objects.link(cam_obj)
            cam_obj.location = loc
            direction = (target[0] - loc[0], target[1] - loc[1], target[2] - loc[2])
            cam_obj.rotation_euler = direction_to_euler(direction)
            cameras.append(cam_obj)

        char_scene.timeline_markers.clear()
        marker_frames = [1, 5, 10, 15, 20]
        for i, cam in enumerate(cameras):
            marker = char_scene.timeline_markers.new(name=f"Cam_{i+1}", frame=marker_frames[i])
            marker.camera = cam

        bg_color = tuple(char_scene.cp_model_sheet_bg_color)

        model_sheet_scene.render.resolution_x = 3000
        model_sheet_scene.render.resolution_y = 1000

        model_sheet_scene.frame_start = 0
        model_sheet_scene.frame_end = 0
        model_sheet_scene.frame_current = 0

        context.window.scene = model_sheet_scene

        if not model_sheet_scene.sequence_editor:
            model_sheet_scene.sequence_editor_create()
        seq_editor = model_sheet_scene.sequence_editor

        for s in list(seq_editor.strips_all):
            seq_editor.strips.remove(s)

        RENDER_FRAME = 1
        model_sheet_scene.frame_start = 1
        model_sheet_scene.frame_end = 1
        model_sheet_scene.frame_current = 1

        model_sheet_scene.view_settings.view_transform = 'Standard'
        model_sheet_scene.view_settings.look = 'None'
        model_sheet_scene.sequencer_colorspace_settings.name = 'sRGB'

        bg = seq_editor.strips.new_effect(
            name="Background",
            type='COLOR',
            channel=1,
            frame_start=-25,
            length=60,
            input1=None,
            input2=None,
        )
        bg.color = bg_color

        strip_width = 600
        strip_length = 30
        for i in range(5):
            fs = -4 - i * 5  # -4, -9, -14, -19, -24
            scene_strip = seq_editor.strips.new_scene(
                name=f"View_{i+1}",
                scene=char_scene,
                channel=2 + i,
                frame_start=fs,
            )
            scene_strip.frame_final_end = fs + strip_length
            scene_strip.scene_camera = cameras[i]
            scene_strip.transform.offset_x = -1200 + i * strip_width

        ve_workspace = bpy.data.workspaces.get("Video Editing")
        for window in context.window_manager.windows:
            if ve_workspace and window.workspace.name == "Video Editing":
                window.scene = model_sheet_scene

        context.window.scene = model_sheet_scene

        self.report({'INFO'}, "Model sheet: video editing layout created")
        return {'FINISHED'}

class CP_OT_set_workbench(bpy.types.Operator):
    bl_idname = "cp.set_workbench"
    bl_label = "Set Workbench"
    def execute(self, context):
        char_scene = bpy.data.scenes.get("Character")
        if not char_scene:
            return {'CANCELLED'}
        char_scene.render.engine = 'BLENDER_WORKBENCH'
        shading = char_scene.display.shading
        shading.type, shading.light, shading.studio_light = 'SOLID', 'STUDIO', 'Default'
        shading.show_cavity, shading.cavity_type = True, 'SCREEN'
        shading.cavity_ridge_factor, shading.cavity_valley_factor = 0.5, 0.5
        self.report({'INFO'}, "Workbench applied")
        return {'FINISHED'}

class CP_OT_set_cycles(bpy.types.Operator):
    bl_idname = "cp.set_cycles"
    bl_label = "Set Cycles"
    def execute(self, context):
        char_scene = bpy.data.scenes.get("Character")
        if not char_scene:
            return {'CANCELLED'}
        char_scene.render.engine = 'CYCLES'
        char_scene.cycles.use_adaptive_sampling, char_scene.cycles.adaptive_threshold, char_scene.cycles.samples = True, 0.1, 128
        char_scene.world = char_scene.world or bpy.data.worlds.new("World_Character")
        char_scene.world.use_nodes = True
        nodes, links = char_scene.world.node_tree.nodes, char_scene.world.node_tree.links
        nodes.clear()
        bg, env, out = nodes.new('ShaderNodeBackground'), nodes.new('ShaderNodeTexEnvironment'), nodes.new('ShaderNodeOutputWorld')
        bg.location, env.location, out.location = (200, 0), (0, 0), (400, 0)
        fp = os.path.join(bpy.utils.resource_path('LOCAL'), "datafiles", "studiolights", "world", "forest.exr")
        if not os.path.exists(fp): fp = os.path.join(bpy.utils.resource_path('GLOBAL'), "datafiles", "studiolights", "world", "forest.exr")
        if os.path.exists(fp): env.image = bpy.data.images.load(fp, check_existing=True)
        links.new(env.outputs['Color'], bg.inputs['Color'])
        links.new(bg.outputs['Background'], out.inputs['Surface'])
        self.report({'INFO'}, "Cycles applied")
        return {'FINISHED'}

class CP_OT_render_model_sheet(bpy.types.Operator):
    bl_idname = "cp.render_model_sheet"
    bl_label = "Render to file"
    def execute(self, context):
        model_sheet_scene = bpy.data.scenes.get("Model Sheet")
        if not model_sheet_scene:
            self.report({'ERROR'}, "Model Sheet scene not found. Press 'Model sheet' button first.")
            return {'CANCELLED'}
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the .blend file first before rendering.")
            return {'CANCELLED'}
        prefs = context.preferences.addons.get(__package__, {}).preferences
        use_transparent = getattr(prefs, 'model_sheet_use_transparent_bg', False)

        if not model_sheet_scene.sequence_editor:
            model_sheet_scene.sequence_editor_create()
        seq_editor = model_sheet_scene.sequence_editor

        bg_strip = next((s for s in seq_editor.strips_all if s.name == "Background"), None)
        if bg_strip:
            seq_editor.strips.remove(bg_strip)

        char_scene = bpy.data.scenes.get("Character")

        if not use_transparent:
            bg_strip = seq_editor.strips.new_effect(name="Background", type='COLOR', channel=1, frame_start=-30, length=60, input1=None, input2=None)
            bg_color_src = char_scene.cp_model_sheet_bg_color if char_scene else (0.8, 0.8, 0.8)
            bg_strip.color = tuple(bg_color_src)
            model_sheet_scene.render.film_transparent = False
            color_mode = 'RGB'
        else:
            model_sheet_scene.render.film_transparent = True
            color_mode = 'RGBA'

        model_sheet_scene.render.use_sequencer, model_sheet_scene.render.use_compositing = True, False
        if char_scene:
            char_scene.render.use_compositing, char_scene.render.use_sequencer = False, False

        char_name = bpy.path.display_name_from_filepath(bpy.data.filepath)
        output_path = os.path.join(os.path.dirname(bpy.data.filepath), f"{char_name}_ModelSheet.png")

        model_sheet_scene.render.filepath = output_path
        model_sheet_scene.render.image_settings.file_format = 'PNG'
        model_sheet_scene.render.image_settings.color_mode = color_mode
        render_pct = char_scene.cp_model_sheet_render_percentage if char_scene else 100
        model_sheet_scene.render.resolution_percentage = render_pct

        prev_scene = context.window.scene
        context.window.scene = model_sheet_scene
        try:
            bpy.ops.render.render(write_still=True)
            self.report({'INFO'}, f"Rendered: {os.path.basename(output_path)}")
            if os.name == 'nt': import winsound; winsound.Beep(500, 300)
            else: print('\a')
        except Exception as e:
            self.report({'ERROR'}, f"Render failed: {e}")
            return {'CANCELLED'}
        finally:
            context.window.scene = prev_scene
        return {'FINISHED'}

class CP_OT_open_readme(bpy.types.Operator):
    bl_idname = "cp.open_readme"
    bl_label = "Open Readme"
    def execute(self, context):
        text_name = "Pipeline_Tracker_README"
        if text_name in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[text_name])
        readme_text = bpy.data.texts.new(name=text_name)
        readme_text.write(
"""Character Pipeline Tracker is an add-on for Blender designed
to organize and automate the pipeline of character creation.
The addon will be useful for both novice artists and professionals.
It helps to standardize and speed up routine operations.
The addon allows you to:
Organize the correct structure of the scene.
Track the stages of the work process.
Prepare the objects for export.
Normalizes names and applies modifiers.
Check the geometry for errors.
Checks the matching of name pairs. Analyzes the mesh for the presence
of non-manifold geometry (problem areas are recorded in Vertices Groups).
Set up a presentation Model Sheet.
Creates a stage for the presentation of a character from different angles.
Simplifies the rendering process.
Export models depending on the stage.
When exporting, the appropriate materials are automatically assigned
and transformations are applied.
Important:
Adhere to the structure of the created collections.
This will help you avoid unexpected mistakes.
Try to follow the original order of the buttons, unless you went back
to the previous steps.
Some model sheet settings are only available in the Model Sheet scene,
in the Video Sequencer window.
The addon allows you to work with several characters in a scene at once.
Some functions work relative to the main collection of the selected object.
Following these rules will ensure stable and automated work with the characters.
""")
        for area in context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                area.spaces[0].text = readme_text
                break
        else:
            bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
            na = context.screen.areas[-1]
            na.type = 'TEXT_EDITOR'
            na.spaces[0].text = readme_text
        self.report({'INFO'}, "Readme opened in Text Editor")
        return {'FINISHED'}

# ========================
# PANELS & PREFERENCES
# ========================
class CP_PT_Panel(bpy.types.Panel):
    bl_label = "Pipeline tracker"
    bl_idname = "CP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Pipeline"
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        split = row.split(factor=0.35, align=True)
        split.label(text="Model name:")
        split.prop(scene, "cp_model_name", text="")
        layout.operator("cp.setup_collections", icon='OUTLINER_OB_GROUP_INSTANCE')

        box = layout.box()
        row = box.row()
        row.prop(scene, "cp_show_pipeline", icon='DISCLOSURE_TRI_DOWN' if scene.cp_show_pipeline else 'DISCLOSURE_TRI_RIGHT', icon_only=True, emboss=False)
        row.label(text="Pipeline tracker")

        if scene.cp_show_pipeline:
            for sec in range(1, TOTAL_SECTIONS + 1):
                section_name = SECTION_NAMES.get(sec, f"Section {sec}")
                count = get_item_count(sec)
                all_done = is_section_complete(scene, sec)
                subbox = box.box()
                row = subbox.row(align=True)
                show_prop = f"cp_show_section_{sec}"
                is_expanded = getattr(scene, show_prop, True)
                icon = 'DISCLOSURE_TRI_DOWN' if is_expanded else 'DISCLOSURE_TRI_RIGHT'
                row.prop(scene, show_prop, icon=icon, icon_only=True, emboss=False)
                row.label(text=section_name)
                if all_done: row.label(text="", icon='CHECKMARK')
                if is_expanded:
                    for item in range(1, count + 1):
                        item_name = f"{sec}.{item} {ITEM_NAMES[sec][item - 1]}"
                        row = subbox.row()
                        prop_name = f"cp_section_{sec}_item_{item}"
                        enabled = is_item_unlocked(scene, sec, item)
                        row.enabled = enabled
                        row.prop(scene, prop_name, text=item_name)
                        if getattr(scene, prop_name, False): row.label(text="", icon='CHECKMARK')

        layout.separator()
        row = layout.row(align=True)
        row.operator("cp.prepare_hp", icon='MESH_DATA')
        row.operator("cp.prepare_lp", icon='MESH_DATA')
        layout.operator("cp.validate_pairs", text='Validate Pairs', icon='CHECKMARK')
        layout.operator("cp.check_lp_mesh", text='Check LP', icon='MESH_DATA')
        layout.operator("cp.clean_scene", text='Clean scene', icon='BRUSH_DATA')
        layout.separator()
        row = layout.row(align=True)
        row.operator("cp.export_bake", text='Export bake', icon='EXPORT')
        row.operator("cp.export_paint", text='Export paint', icon='EXPORT')
        row = layout.row()
        split = row.split(factor=0.7, align=True)
        split.operator("cp.final_export", text='Final export', icon='FILE_TICK')
        split.prop(scene, "cp_export_format", text="")
        layout.separator()
        layout.operator("cp.model_sheet", text='Model sheet', icon='CAMERA_DATA')
        row = layout.row(align=True)
        row.operator("cp.set_workbench", text='Workbench', icon='SHADING_RENDERED')
        row.operator("cp.set_cycles", text='Cycles', icon='SHADING_TEXTURE')
        row = layout.row(align=True)
        row.prop(context.scene, "cp_model_sheet_render_percentage", text="%")
        row.separator()
        prefs = context.preferences.addons.get(__package__, {}).preferences
        if prefs and getattr(prefs, 'model_sheet_use_transparent_bg', False):
            row.label(text="Transparent")
        else:
            row.prop(context.scene, "cp_model_sheet_bg_color", text="")
        row.separator()
        if prefs: row.prop(prefs, "model_sheet_use_transparent_bg", text="", toggle=False)
        layout.operator("cp.render_model_sheet", text='Render to file', icon='RENDER_STILL')

class CP_PT_header_content(bpy.types.Panel):
    bl_idname = "CP_PT_header_content"
    bl_label = "Pipeline tracker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    def draw(self, context): CP_PT_Panel.draw(self, context)

class CP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    show_header_button: bpy.props.BoolProperty(name="Show Header Button", default=True)
    model_sheet_use_transparent_bg: bpy.props.BoolProperty(name="Model Sheet Transparent Background", default=False)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_header_button")
        layout.prop(self, "model_sheet_use_transparent_bg")
        layout.separator()
        layout.operator("cp.open_readme", icon='TEXT')

# ========================
# PROPERTIES & STATE
# ========================
_last_state = {}
def on_item_update(self, context):
    global _last_state
    scene = context.scene
    if not _last_state:
        for sec in range(1, TOTAL_SECTIONS + 1):
            count = get_item_count(sec)
            for item in range(1, count + 1):
                prop = f"cp_section_{sec}_item_{item}"
                _last_state[prop] = getattr(scene, prop, False)
        return

    changed_prop = None
    current_value = None
    for sec in range(1, TOTAL_SECTIONS + 1):
        count = get_item_count(sec)
        for item in range(1, count + 1):
            prop = f"cp_section_{sec}_item_{item}"
            current = getattr(scene, prop, False)
            prev = _last_state.get(prop, False)
            if current != prev:
                changed_prop = prop
                current_value = current
                _last_state[prop] = current
                break
        if changed_prop: break

    if not changed_prop or not current_value: return

    parts = changed_prop.split('_')
    sec = int(parts[2])
    item = int(parts[4])

    count = get_item_count(sec)
    for i in range(item + 1, count + 1):
        prop_name = f"cp_section_{sec}_item_{i}"
        setattr(scene, prop_name, False)
        _last_state[prop_name] = False

    for s in range(sec + 1, TOTAL_SECTIONS + 1):
        s_count = get_item_count(s)
        for j in range(1, s_count + 1):
            prop_name = f"cp_section_{s}_item_{j}"
            setattr(scene, prop_name, False)
            _last_state[prop_name] = False

    if is_section_complete(scene, sec):
        show_prop = f"cp_show_section_{sec}"
        if hasattr(scene, show_prop): setattr(scene, show_prop, False)
        next_sec = sec + 1
        if next_sec <= TOTAL_SECTIONS and is_section_unlocked(scene, next_sec):
            next_show_prop = f"cp_show_section_{next_sec}"
            if hasattr(scene, next_show_prop): setattr(scene, next_show_prop, True)

def register_props():
    for sec in range(1, TOTAL_SECTIONS + 1):
        count = get_item_count(sec)
        for item in range(1, count + 1):
            prop_name = f"cp_section_{sec}_item_{item}"
            setattr(bpy.types.Scene, prop_name, bpy.props.BoolProperty(default=False, update=on_item_update))
        setattr(bpy.types.Scene, f"cp_show_section_{sec}", bpy.props.BoolProperty(default=True))
    bpy.types.Scene.cp_model_name = bpy.props.StringProperty(name="Model name", default="")
    bpy.types.Scene.cp_show_pipeline = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.cp_export_format = bpy.props.EnumProperty(name="Export Format", items=[('FBX','FBX',''),('OBJ','OBJ',''),('GLB','glTF Binary (.glb)','')], default='FBX')
    bpy.types.Scene.cp_model_sheet_render_percentage = bpy.props.IntProperty(name="Render Scale %", min=1, max=100, default=100)
    bpy.types.Scene.cp_model_sheet_bg_color = bpy.props.FloatVectorProperty(name="Model Sheet Background Color", subtype='COLOR_GAMMA', size=3, min=0.0, max=1.0, default=(0.8, 0.8, 0.8))

def unregister_props():
    global _last_state
    for sec in range(1, TOTAL_SECTIONS + 1):
        for item in range(1, get_item_count(sec) + 1):
            prop_name = f"cp_section_{sec}_item_{item}"
            if hasattr(bpy.types.Scene, prop_name): delattr(bpy.types.Scene, prop_name)
        if hasattr(bpy.types.Scene, f"cp_show_section_{sec}"): delattr(bpy.types.Scene, f"cp_show_section_{sec}")
    for attr in ["cp_model_name", "cp_show_pipeline", "cp_export_format", "cp_model_sheet_render_percentage", "cp_model_sheet_bg_color"]:
        if hasattr(bpy.types.Scene, attr): delattr(bpy.types.Scene, attr)
    _last_state.clear()

# ========================
# ICONS & HEADER
# ========================
def load_custom_icons():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    icon_path = Path(__file__).parent / "icons" / "icon.png"
    if icon_path.exists(): pcoll.load("pipeline", str(icon_path), 'IMAGE')
    bpy.types.WindowManager.cp_icons = pcoll

def unload_custom_icons():
    if hasattr(bpy.types.WindowManager, "cp_icons"):
        bpy.utils.previews.remove(bpy.types.WindowManager.cp_icons)
        del bpy.types.WindowManager.cp_icons

def draw_pipeline_menu(self, context):
    prefs = context.preferences.addons.get(__package__, {}).preferences
    if prefs and not getattr(prefs, 'show_header_button', True): return
    layout, scene = self.layout, context.scene
    current_text = "Ready"
    for sec_idx, section in enumerate(SECTION_NAMES.values()):
        sec_num = sec_idx + 1
        if not is_section_complete(scene, sec_num):
            for item_idx, item in enumerate(ITEM_NAMES[sec_num]):
                item_prop = f"cp_section_{sec_num}_item_{item_idx + 1}"
                if not getattr(scene, item_prop, False):
                    current_text = f"{section} — {item}"
                    break
            break
    icon_value = 0
    if hasattr(bpy.types.WindowManager, "cp_icons") and "pipeline" in bpy.types.WindowManager.cp_icons:
        icon_value = bpy.types.WindowManager.cp_icons["pipeline"].icon_id
    layout.popover(panel="CP_PT_header_content", text=current_text, icon_value=icon_value)
    layout.separator()

# ========================
# REGISTER / UNREGISTER
# ========================
classes = (
    CP_OT_setup_collections, CP_OT_prepare_hp, CP_OT_prepare_lp, CP_OT_validate_pairs,
    CP_OT_check_lp_mesh, CP_OT_toggle_high_visibility, CP_OT_toggle_low_visibility,
    CP_OT_clean_scene, CP_OT_export_bake, CP_OT_export_paint, CP_OT_final_export,
    CP_PT_Panel, CP_PT_header_content, CP_preferences, CP_OT_model_sheet,
    CP_OT_set_workbench, CP_OT_set_cycles, CP_OT_render_model_sheet, CP_OT_open_readme,
)

def register():
    load_custom_icons()
    register_props()
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_editor_menus.append(draw_pipeline_menu)

def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_pipeline_menu)
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except: pass
    unregister_props()
    unload_custom_icons()

if __name__ == "__main__":
    register()