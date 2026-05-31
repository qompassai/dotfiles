# --- START OF FILE __init__.py ---

bl_info = {
    "name": "Surface Diagnostics",
    "author": "Josef Ludvík Böhm",
    "version": (1, 4, 3),
    "blender": (4, 5, 0),
    "location": "View3D > UI > Surf Ace",
    "description": "Set of tools for diagnosing surface quality for technical surfacing",
    "warning": "",
    "doc_url": "https://discord.gg/cWVT9a6sNe",
    "tracker_url": "https://superhivemarket.com/products/surface-diagnostics",
    "support": "COMMERCIAL",
    "category": "Mesh",
    "license": "GPL-3.0-or-later",
}

import bpy
import bpy.utils.previews
import bmesh
import os

# --- Constants ---

ADDON_BLEND_FILENAME = "Surface_Diagnostics_Addon_B4.5_1.4.3.blend"
ADDON_BLEND_FILE_PATH = os.path.join(os.path.dirname(__file__), "assets", ADDON_BLEND_FILENAME)

# Common names and prefixes
SD_PREFIX = "SD_"
MOD_MAT_OVERRIDE = f"{SD_PREFIX}Mat_Override"
MOD_CGRAPH = f"{SD_PREFIX}CGraph"
MOD_ANGLEGRAPH = f"{SD_PREFIX}AngleGraph"
MOD_SECTIONS_GEOM = f"{SD_PREFIX}SectionsGeometry"
MOD_SECTIONS_CUT_GEOM = f"{SD_PREFIX}SectionsCutGeometry"
MOD_EXTREMES = f"{SD_PREFIX}Extremes"
MOD_PROXIMITY = f"{SD_PREFIX}Proximity"
MOD_MINMAX_RADIUS = f"{SD_PREFIX}MinMax_Radius"
MOD_DRAFT_ANGLE = f"{SD_PREFIX}Draft_Angle"
MOD_CURVATURE = f"{SD_PREFIX}Curvature"

MAT_ZEBRA = f"{SD_PREFIX}Zebra"
MAT_ISOANGLE = f"{SD_PREFIX}Isoangle_Lines"
MAT_SECTION_LINES = f"{SD_PREFIX}Section_Lines"
MAT_SECTION_CUT = f"{SD_PREFIX}Section_Cut"
MAT_PROXIMITY = f"{SD_PREFIX}Proximity"
MAT_DRAFT_ANGLE = f"{SD_PREFIX}Draft_Angle"
MAT_MINMAX_RADIUS = f"{SD_PREFIX}MinMax_Radius"
MAT_CURVATURE = f"{SD_PREFIX}Curvature"

EMPTY_COORD_SUFFIX = "_Coordinates"
EMPTY_SECTIONS_COORD = f"{SD_PREFIX}Sections_Coordinates"

# --- Globals ---
_icons = None

# --- Addon Preferences ---

class SurfaceDiagnosticsAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    debug_mode: bpy.props.BoolProperty(
        name="Debug Mode",
        description="Enable to print debug information to the system console",
        default=False,
    )

    legacy_sections_cut: bpy.props.BoolProperty(
        name="Legacy Sections/Cut",
        description="Show legacy Geometry Sections and Sections Cut tools (Material Override)",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "debug_mode")
        col.prop(self, "legacy_sections_cut")

def debug_print(*args, **kwargs):
    """Custom print function that only prints if debug mode is enabled."""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.debug_mode:
            print(*args, **kwargs)
    except (AttributeError, KeyError):
        pass

# --- Utility Functions ---

def string_to_int(value):
    """Safely convert a string to an integer, returning 0 on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def get_icon_id(icon_name):
    """Get the icon ID from a string name or integer value."""
    enum_items = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items
    if icon_name in enum_items:
        return enum_items[icon_name].value

    global _icons
    if _icons and icon_name in _icons:
        return _icons[icon_name].icon_id

    return string_to_int(icon_name)

def load_icons(icons_dict):
    """Loads custom icons into the preview collection."""
    global _icons
    if not isinstance(_icons, bpy.utils.previews.ImagePreviewCollection):
        return

    script_path = os.path.dirname(__file__)
    icons_subfolder = "icons"

    for name, filename in icons_dict.items():
        rel_path = os.path.join(script_path, icons_subfolder, filename)
        if os.path.exists(rel_path):
            _icons.load(name, rel_path, 'IMAGE')
        else:
            debug_print(f"Warning: Icon file not found: {rel_path}")

# --- Asset Loading ---

ASSET_UUID_MAP = {
    "materials": {
        # --- Active Materials (Used in UI/Operators) ---
        MAT_ZEBRA:           "SD_Zebra_8OPX6",
        MAT_ISOANGLE:        "SD_Isoangle_Lines_89KEQ",
        MAT_SECTION_LINES:   "SD_Section_Lines_D8ACT",
        MAT_SECTION_CUT:     "SD_Section_Cut_2WLLP",
        MAT_PROXIMITY:       "SD_Proximity_76LLR",
        MAT_DRAFT_ANGLE:     "SD_Draft_Angle_2X6VQ",
        MAT_MINMAX_RADIUS:   "SD_MinMax_Radius_6W4CY",
        MAT_CURVATURE:       "SD_Curvature_AVW4L",

        # --- Internal Dependencies (Auto-loaded only) ---
        "SD_Curvature_bands": "SD_Curvature_bands_N8G05",
    },
    "node_groups": {
        # --- Active Modifiers (Used in UI/Operators) ---
        MOD_MAT_OVERRIDE:       "SD_Mat_Override_MD6L4",
        MOD_SECTIONS_GEOM:      "SD_SectionsGeometry_CUIF8",
        MOD_SECTIONS_CUT_GEOM:  "SD_SectionsCutGeometry_CXIF9",
        MOD_PROXIMITY:          "SD_Proximity_5IQDL",
        MOD_DRAFT_ANGLE:        "SD_Draft_Angle_XWCYF",
        MOD_MINMAX_RADIUS:      "SD_MinMax_Radius_5H7OW",
        MOD_CURVATURE:          "SD_Curvature_6SH8I",
        MOD_CGRAPH:             "SD_CGraph_7Q1TG",
        MOD_ANGLEGRAPH:         "SD_AngleGraph_7OB80",
        MOD_EXTREMES:           "SD_Extremes_VMNAA",

        # --- Internal Dependencies (Auto-loaded only) ---
        "SD_AGraph_Scale":             "SD_AGraph_Scale_YAYPM",
        "SD_CGraph_Scale":             "SD_CGraph_Scale_EBHYE",
        "SD_curvature_A on B lenght":  "SD_curvature_A on B lenght_6VKDN",
        "SD_def. circumcircle":        "SD_def. circumcircle_WTMIL",
        "SD_radius_A on B lenght":     "SD_radius_A on B lenght_I7MDQ",
        "SD_show angle extremes":      "SD_show angle extremes_B6NT5",
        "SD_show cgraph extremes":     "SD_show cgraph extremes_B7Y0B",
        "SD_Show extreme values":      "SD_Show extreme values_PAPOC",
        "SD_show sample_angle":        "SD_show sample_angle_XCX42",
        "SD_show sample_value":        "SD_show sample_value_OCD0N",
    }
}

def get_or_append_asset(asset_type, friendly_name):
    """
    Gets an asset from the current scene, or appends it from the library file if not found.
    Uses a custom property 'SD_UUID' to identify addon assets robustly.
    """
    uuid_value = ASSET_UUID_MAP.get(asset_type, {}).get(friendly_name)
    if not uuid_value:
        print(f"Error: Asset '{friendly_name}' of type '{asset_type}' not found in the ASSET_UUID_MAP.")
        return None

    # 1. Search for existing asset in the scene with the correct UUID
    data_collection = getattr(bpy.data, asset_type)
    for asset in data_collection:
        if asset.get("SD_UUID") == uuid_value:
            return asset

    # 2. If not found, derive the internal name and load from library
    if not os.path.exists(ADDON_BLEND_FILE_PATH):
        print(f"Error: Addon blend file not found at '{ADDON_BLEND_FILE_PATH}'")
        return None

    try:
        internal_name = uuid_value.rsplit('_', 1)[0]
        debug_print(f"Loading '{internal_name}' from library...")

        with bpy.data.libraries.load(ADDON_BLEND_FILE_PATH, link=False) as (data_from, data_to):
            if internal_name in getattr(data_from, asset_type):
                setattr(data_to, asset_type, [internal_name])
            else:
                print(f"Error: Cannot find asset '{internal_name}' in library file.")
                return None

        bpy.context.view_layer.update()

        for asset in data_collection:
            if asset.get("SD_UUID") == uuid_value:
                return asset

        return None

    except Exception as e:
        print(f"Error loading from library to find UUID '{uuid_value}': {e}")
        return None


# --- Object & Modifier Management ---

def get_or_create_shared_sections_empty(context):
    """Gets or creates the shared Empty object for all sectioning tools."""
    empty_name = EMPTY_SECTIONS_COORD
    coord_empty = bpy.data.objects.get(empty_name)

    if coord_empty:
        if not coord_empty.users_collection:
            try:
                context.scene.collection.objects.link(coord_empty)
            except RuntimeError:
                pass
    else:
        coord_empty = bpy.data.objects.new(name=empty_name, object_data=None)
        coord_empty.location = context.scene.cursor.location
        coord_empty.empty_display_type = 'ARROWS'
        context.scene.collection.objects.link(coord_empty)

    return coord_empty

def ensure_coordinate_empty(context, mat_name):
    """Creates or links an Empty object used for texture coordinates."""
    coord_node_name = 'Texture Coordinate'
    target_material = get_or_append_asset("materials", mat_name)

    if not target_material or not target_material.node_tree or coord_node_name not in target_material.node_tree.nodes:
         return

    coord_node = target_material.node_tree.nodes[coord_node_name]
    coord_empty = None

    if mat_name in {MAT_SECTION_LINES, MAT_SECTION_CUT}:
        coord_empty = get_or_create_shared_sections_empty(context)
    else:
        empty_name = mat_name + EMPTY_COORD_SUFFIX
        coord_empty = bpy.data.objects.get(empty_name)

        if coord_empty:
            if not coord_empty.users_collection:
                try:
                    context.scene.collection.objects.link(coord_empty)
                except RuntimeError:
                    pass
        else:
            coord_empty = bpy.data.objects.new(name=empty_name, object_data=None)
            coord_empty.location = context.scene.cursor.location
            coord_empty.empty_display_type = 'ARROWS'
            context.scene.collection.objects.link(coord_empty)

    if coord_empty:
        coord_node.object = coord_empty

def add_geometry_nodes_modifier(obj, mod_name, node_group_name):
    """Adds a Geometry Nodes modifier to an object or returns existing one."""
    node_group = get_or_append_asset("node_groups", node_group_name)
    if not node_group:
        print(f"Error: Node group '{node_group_name}' not found.")
        return None

    if mod_name in obj.modifiers:
        modifier = obj.modifiers[mod_name]
        if modifier.type == 'NODES':
            modifier.node_group = node_group
            return modifier
        else:
            return None

    modifier = obj.modifiers.new(name=mod_name, type='NODES')
    modifier.node_group = node_group
    return modifier

def setup_gn_modifier_inputs(modifier, inputs_dict):
    """Sets multiple inputs on a Geometry Nodes modifier."""
    if not modifier or modifier.type != 'NODES':
        return
    for input_name, value in inputs_dict.items():
        try:
            modifier[input_name] = value
        except (TypeError, KeyError):
             debug_print(f"Warning: Could not set input '{input_name}' on modifier '{modifier.name}'.")

def remove_modifier(obj, mod_name):
    """Safely removes a modifier by name if it exists."""
    if mod_name in obj.modifiers:
        mod = obj.modifiers[mod_name]
        obj.modifiers.remove(modifier=mod)
        return True
    return False

def create_graph_object_and_modifier(context, base_name, mod_type_name):
    """Creates a new MESH object and adds a GN modifier for graph visualization."""
    graph_ob_name = base_name

    # Always create a new object to allow Blender to generate unique names
    graph_mesh = bpy.data.meshes.new(name=graph_ob_name)
    graph_ob = bpy.data.objects.new(name=graph_ob_name, object_data=graph_mesh)
    graph_ob.location = context.scene.cursor.location
    context.scene.collection.objects.link(graph_ob)

    if mod_type_name != MOD_SECTIONS_GEOM:
        graph_ob.show_in_front = True

    modifier = add_geometry_nodes_modifier(graph_ob, graph_ob.name, mod_type_name)

    if modifier:
        return modifier, graph_ob
    else:
        if graph_ob:
            bpy.data.objects.remove(graph_ob, do_unlink=True)
        if graph_mesh and graph_mesh.users == 0:
            bpy.data.meshes.remove(graph_mesh)
        return None, None


# --- Attribute and Selection Management ---

def get_edit_bmesh(obj):
    """Gets a bmesh from an object in Edit Mode."""
    if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
        return bmesh.from_edit_mesh(obj.data)
    return None

def get_unique_name(base_name, collection):
    """Generates a unique name for an item in a Blender collection."""
    if base_name not in collection:
        return base_name
    i = 1
    while True:
        unique_name = f"{base_name}.{i:03d}"
        if unique_name not in collection:
            return unique_name
        i += 1

def create_graph_attribute_from_selection(context, obj, attr_basename, domain='EDGE'):
    """
    Creates/Updates INT attribute based on Edit Mode selection using bmesh.
    Returns the full attribute name or None on failure.
    """
    if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
        debug_print("Error: create_graph_attribute_from_selection requires MESH object in EDIT mode.")
        return None

    base_name = f"{obj.name}_{attr_basename}"
    attr_name = get_unique_name(base_name, obj.data.attributes)

    bm = get_edit_bmesh(obj)
    if not bm:
        return None

    try:
        if domain == 'EDGE':
            layer_collection = bm.edges.layers.int
            elements = bm.edges
        elif domain == 'FACE':
            layer_collection = bm.faces.layers.int
            elements = bm.faces
        else:
            raise ValueError(f"Unsupported domain: {domain}")

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        layer = layer_collection.get(attr_name)
        if not layer:
             layer = layer_collection.new(attr_name)

        modified_count = 0
        selected_count = 0
        for elem in elements:
            target_value = 1 if elem.select else 0
            if elem[layer] != target_value:
                 elem[layer] = target_value
                 modified_count += 1
            if elem.select:
                 selected_count += 1

        if selected_count == 0:
             debug_print(f"Warning: No elements selected in domain '{domain}'.")

        if modified_count > 0:
            bmesh.update_edit_mesh(obj.data)
            return layer.name
        else:
             return layer.name

    except Exception as e:
        debug_print(f"Error processing attribute '{attr_name}': {e}")
        return None

def assign_attribute_to_modifier_input(modifier, input_id, attr_name):
    """Configures a modifier input to use a named attribute."""
    if not modifier or not attr_name: return

    prefix = None
    if f"Input_{input_id}_use_attribute" in modifier:
        prefix = "Input_"
    elif f"Socket_{input_id}_use_attribute" in modifier:
        prefix = "Socket_"

    if not prefix:
        return

    try:
        modifier[f"{prefix}{input_id}_use_attribute"] = True
        modifier[f"{prefix}{input_id}_attribute_name"] = attr_name
    except Exception as e:
        debug_print(f"Warning: Error assigning attribute: {e}")

def remove_mesh_attribute(obj, attr_name):
    """Removes an attribute from an object's mesh data if it exists."""
    if obj and obj.type == 'MESH' and obj.data and hasattr(obj.data, 'attributes') and attr_name in obj.data.attributes:
        try:
            attr = obj.data.attributes[attr_name]
            obj.data.attributes.remove(attr)
            return True
        except Exception as e:
            debug_print(f"Error removing attribute: {e}")
    return False

def remove_data_by_prefix(data_collection, prefix):
    """Removes unused data-blocks starting with a prefix."""
    if not hasattr(bpy.data, data_collection):
        return

    collection = getattr(bpy.data, data_collection)
    items_to_check = list(collection)
    for item in items_to_check:
        try:
            if item.name.startswith(prefix) and item.users == 0:
                collection.remove(item)
        except ReferenceError:
             continue

def cleanup_unused_sd_data():
    """Removes unused materials and node groups created by this addon."""
    remove_data_by_prefix("materials", SD_PREFIX)
    remove_data_by_prefix("node_groups", SD_PREFIX)

def cleanup_associated_data(obj_name, graph_type_prefix):
    """Removes the graph object, mesh, and attribute associated with a graph type."""
    debug_print(f"Cleaning up data for '{obj_name}' / '{graph_type_prefix}'")

    source_obj = bpy.data.objects.get(obj_name)
    target_attr_name = None

    # 1. Attempt to find the specific attribute linking to the graph
    if source_obj and source_obj.type == 'MESH' and source_obj.data:
        prefix = f"{obj_name}_{graph_type_prefix}"
        for attr in source_obj.data.attributes:
            if attr.name.startswith(prefix):
                target_attr_name = attr.name
                break

    # Fallback: Guess the name if attribute missing
    if not target_attr_name:
        target_attr_name = f"{obj_name}_{graph_type_prefix}"

    # 2. Remove Attribute
    if source_obj:
        remove_mesh_attribute(source_obj, target_attr_name)

    # 3. Remove Graph Object and its Data
    graph_ob = bpy.data.objects.get(target_attr_name)

    if graph_ob:
        mesh_data = graph_ob.data
        try:
            bpy.data.objects.remove(graph_ob, do_unlink=True)
        except Exception:
            pass

        # Cleanup the mesh data block if it's now orphaned
        if mesh_data and mesh_data.users == 0:
            try:
                bpy.data.meshes.remove(mesh_data)
            except Exception:
                pass
    else:
        # Handle case where Object is gone but Mesh data remains
        orphan_mesh = bpy.data.meshes.get(target_attr_name)
        if orphan_mesh and orphan_mesh.users == 0:
             try:
                 bpy.data.meshes.remove(orphan_mesh)
             except Exception:
                 pass

# --- Operators ---

class SNA_OT_UnhideAllDiagnosticTools(bpy.types.Operator):
    """Shows or Hides all Surface Diagnostics modifiers and objects"""
    bl_idname = "sna.unhide_all_diagnostic_tools"
    bl_label = "Toggle Diagnostics Visibility"
    bl_description = "Globally show or hide all diagnostic modifiers and graph objects"
    bl_options = {"REGISTER", "UNDO"}

    show: bpy.props.BoolProperty(
        name='Show',
        default=False,
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        target_state = self.show

        # Modifiers
        for obj in context.scene.objects:
            if not hasattr(obj, "modifiers"): continue
            for mod in obj.modifiers:
                if SD_PREFIX in mod.name:
                    try:
                        mod.show_viewport = target_state
                        mod.show_render = target_state
                    except TypeError:
                         pass

        # Graph Objects
        for obj in context.scene.objects:
            if SD_PREFIX in obj.name:
                obj.hide_viewport = not target_state
                obj.hide_render = not target_state

        context.scene.sna_visibility_switch = target_state
        return {"FINISHED"}

class SNA_OT_RemoveGraphObject(bpy.types.Operator):
    """Removes a specific Graph Object, its mesh data, and the associated attribute"""
    bl_idname = "sna.remove_graph_object"
    bl_label = "Remove Graph Object"
    bl_description = "Removes selected Graph Object, its mesh data, and the driving attribute"
    bl_options = {"REGISTER", "UNDO"}

    graph_object_name: bpy.props.StringProperty(name="Graph Object Name")
    source_object_name: bpy.props.StringProperty(name="Source Object Name")
    graph_type: bpy.props.StringProperty(name="Graph Type Prefix")

    @classmethod
    def poll(cls, context):
         return True

    def execute(self, context):
        cleanup_associated_data(self.source_object_name, self.graph_type)
        cleanup_unused_sd_data()
        return {"FINISHED"}

class SNA_OT_AddMaterialOverride(bpy.types.Operator):
    """Applies a diagnostic material using a Geometry Nodes override modifier"""
    bl_idname = "sna.add_material_override"
    bl_label = "Apply Diagnostic Material"
    bl_description = "Creates/updates GN Modifier for diagnostic material override"
    bl_options = {"REGISTER", "UNDO"}

    mat_name: bpy.props.StringProperty(name="Material Name")
    node_group_name: bpy.props.StringProperty(name="Node Group Name")
    input_socket_name: bpy.props.StringProperty(name="Material Input Socket")

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.select_get() and \
               any(o.type in {'MESH', 'CURVE'} and o.library is None for o in context.selected_editable_objects)

    def _handle_extremes(self, context, obj):
        extremes_nodegroup = MOD_EXTREMES
        extremes_obj_name = f"{obj.name}_{extremes_nodegroup}"

        cleanup_associated_data(obj.name, MOD_EXTREMES)

        modifier, graph_ob = create_graph_object_and_modifier(context, extremes_obj_name, extremes_nodegroup)
        if modifier and graph_ob:
             setup_gn_modifier_inputs(modifier, {'Input_2': obj})
             return True
        return False

    def execute(self, context):
        node_group = get_or_append_asset("node_groups", self.node_group_name)
        material = get_or_append_asset("materials", self.mat_name)

        if not node_group or not material:
            self.report({'ERROR'}, "Could not load assets.")
            return {'CANCELLED'}

        needs_extremes = self.node_group_name in {MOD_PROXIMITY, MOD_MINMAX_RADIUS}
        needs_coords_empty = self.mat_name in {MAT_SECTION_LINES, MAT_SECTION_CUT}

        selected_objects = [o for o in context.selected_editable_objects if o.type in {'MESH', 'CURVE'}]
        if not selected_objects:
             return {'CANCELLED'}

        for obj in selected_objects:
            mod_name = MOD_MAT_OVERRIDE
            attr_basename = MOD_MAT_OVERRIDE
            full_attr_name = f"{obj.name}_{attr_basename}"

            remove_modifier(obj, mod_name)
            remove_mesh_attribute(obj, full_attr_name)

            modifier = add_geometry_nodes_modifier(obj, mod_name, self.node_group_name)
            if not modifier: continue

            setup_gn_modifier_inputs(modifier, {self.input_socket_name: material})

            input_id_for_selection = '37'
            input_prop_name = f'Input_{input_id_for_selection}'
            socket_prop_name = f'Socket_{input_id_for_selection}'
            has_attribute_input_37 = input_prop_name in modifier or socket_prop_name in modifier

            if has_attribute_input_37 and context.mode == 'EDIT_MESH' and obj.type == 'MESH':
                created_attr_name = create_graph_attribute_from_selection(context, obj, attr_basename, domain='FACE')
                if created_attr_name:
                    assign_attribute_to_modifier_input(modifier, input_id_for_selection, created_attr_name)

            if needs_extremes:
                self._handle_extremes(context, obj)
            if needs_coords_empty:
                ensure_coordinate_empty(context, self.mat_name)

        return {"FINISHED"}

class SNA_OT_CreateAngleGraph(bpy.types.Operator):
    """Creates a new Angle Graph based on selected edges in Edit Mode"""
    bl_idname = "sna.create_angle_graph"
    bl_label = "Angle Graph"
    bl_description = "Creates new Angle Graph modifier from selected edges"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.data and obj.type == 'MESH'):
            return False

        if context.mode == 'OBJECT':
            return obj.select_get()
        if context.mode == 'EDIT_MESH':
            mesh = obj.data
            return mesh.total_vert_sel > 0 or mesh.total_edge_sel > 0 or mesh.total_face_sel > 0

        return False

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or not active_obj.data:
             self.report({'ERROR'}, "Invalid active object or object data.")
             return {'CANCELLED'}

        mod_type_name = MOD_ANGLEGRAPH
        input_id_for_attribute = '7'
        input_id_for_source_obj = 'Input_13'

        # --- Edit Mode (Mesh) ---
        if context.mode == 'EDIT_MESH':
            if not (active_obj.data.total_vert_sel > 0 or active_obj.data.total_edge_sel > 0 or active_obj.data.total_face_sel > 0):
                 self.report({'WARNING'}, "No vertices, edges, or faces selected.")
                 return {'CANCELLED'}

            attr_name = create_graph_attribute_from_selection(context, active_obj, mod_type_name, domain='EDGE')
            if not attr_name:
                self.report({'ERROR'}, "Failed to create edge attribute.")
                return {'CANCELLED'}

            modifier, graph_ob = create_graph_object_and_modifier(context, attr_name, mod_type_name)
            if not modifier or not graph_ob:
                remove_mesh_attribute(active_obj, attr_name)
                self.report({'ERROR'}, "Failed to create graph object or modifier.")
                return {'CANCELLED'}

            setup_gn_modifier_inputs(modifier, {input_id_for_source_obj: active_obj})
            assign_attribute_to_modifier_input(modifier, input_id_for_attribute, attr_name)
            graph_ob.color = active_obj.color

        # --- Object Mode (Mesh) ---
        elif context.mode == 'OBJECT':
            cleanup_associated_data(active_obj.name, mod_type_name)

            # Create a unique attribute for all edges
            attr_basename = f"{active_obj.name}_{mod_type_name}"
            attr_name = get_unique_name(attr_basename, active_obj.data.attributes)

            try:
                attr = active_obj.data.attributes.new(name=attr_name, type='INT', domain='EDGE')
                values = [1] * len(active_obj.data.edges)
                attr.data.foreach_set('value', values)
            except Exception as e:
                debug_print(f"Error creating all-edge attribute: {e}")
                self.report({'ERROR'}, "Failed to create all-edge attribute.")
                return {'CANCELLED'}

            # Name the graph object after the attribute for consistency
            modifier, graph_ob = create_graph_object_and_modifier(context, attr_name, mod_type_name)
            if not modifier or not graph_ob:
                remove_mesh_attribute(active_obj, attr_name) # Cleanup
                self.report({'ERROR'}, "Failed to create graph object or modifier.")
                return {'CANCELLED'}

            graph_ob.color = active_obj.color
            setup_gn_modifier_inputs(modifier, {input_id_for_source_obj: active_obj})
            assign_attribute_to_modifier_input(modifier, input_id_for_attribute, attr_name)

        else:
             self.report({'ERROR'}, f"Invalid mode for AngleGraph creation: {context.mode}")
             return {'CANCELLED'}
             
        return {"FINISHED"}

class SNA_OT_CreateCurvatureGraph(bpy.types.Operator):
    """Creates a new Curvature Graph for selected edges/faces or a whole curve/mesh"""
    bl_idname = "sna.create_curvature_graph"
    bl_label = "Curvature Graph"
    bl_description = "Creates new object with Curvature Graph modifier"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.data):
            return False
        
        if context.mode == 'OBJECT':
            return obj.select_get() and obj.type in {'MESH', 'CURVE'}
        elif context.mode == 'EDIT_MESH':
            if obj.type == 'MESH':
                mesh = obj.data
                return mesh.total_vert_sel > 0 or mesh.total_edge_sel > 0 or mesh.total_face_sel > 0
        
        return False

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or not active_obj.data:
             self.report({'ERROR'}, "Invalid active object or object data.")
             return {'CANCELLED'}

        mod_type_name = MOD_CGRAPH
        input_id_for_attribute = '7'
        input_id_for_source_obj = 'Input_13'
        input_id_for_curve_mode = 'Input_11'

        # --- Edit Mode (Mesh) ---
        if active_obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            mesh_data = active_obj.data
            if not (mesh_data.total_vert_sel > 0 or mesh_data.total_edge_sel > 0 or mesh_data.total_face_sel > 0):
                 self.report({'WARNING'}, "No vertices, edges, or faces selected.")
                 return {'CANCELLED'}

            # Always request EDGE domain
            attr_name = create_graph_attribute_from_selection(context, active_obj, mod_type_name, domain='EDGE')

            if not attr_name:
                self.report({'ERROR'}, "Failed to create mesh attribute.")
                return {'CANCELLED'}

            modifier, graph_ob = create_graph_object_and_modifier(context, attr_name, mod_type_name)
            if not modifier or not graph_ob:
                remove_mesh_attribute(active_obj, attr_name)
                self.report({'ERROR'}, "Failed to create graph object or modifier.")
                return {'CANCELLED'}

            setup_gn_modifier_inputs(modifier, {
                input_id_for_source_obj: active_obj,
                input_id_for_curve_mode: False
            })
            assign_attribute_to_modifier_input(modifier, input_id_for_attribute, attr_name)

        # --- Object Mode (Mesh or Curve) ---
        elif context.mode == 'OBJECT':
            is_curve = (active_obj.type == 'CURVE')

            cleanup_associated_data(active_obj.name, mod_type_name)

            graph_ob_name = f"{active_obj.name}_{mod_type_name}"
            modifier, graph_ob = create_graph_object_and_modifier(context, graph_ob_name, mod_type_name)
            if not modifier or not graph_ob:
                self.report({'ERROR'}, "Failed to create graph object or modifier.")
                return {'CANCELLED'}

            inputs_to_set = {
                input_id_for_source_obj: active_obj,
                input_id_for_curve_mode: is_curve,
            }

            # Disable attribute usage, set default to 1.0
            input7_key = None; socket7_key = None; input7_val_key = None; socket7_val_key = None
            if f"Input_{input_id_for_attribute}_use_attribute" in modifier:
                input7_key = f"Input_{input_id_for_attribute}_use_attribute"
                input7_val_key = f"Input_{input_id_for_attribute}"
            elif f"Socket_{input_id_for_attribute}_use_attribute" in modifier:
                socket7_key = f"Socket_{input_id_for_attribute}_use_attribute"
                socket7_val_key = f"Socket_{input_id_for_attribute}"

            if input7_key: inputs_to_set[input7_key] = False
            elif socket7_key: inputs_to_set[socket7_key] = False

            if input7_val_key and input7_val_key in modifier: inputs_to_set[input7_val_key] = 1.0
            elif socket7_val_key and socket7_val_key in modifier: inputs_to_set[socket7_val_key] = 1.0

            setup_gn_modifier_inputs(modifier, inputs_to_set)

        else:
             self.report({'ERROR'}, f"Invalid mode for CGraph creation: {context.mode}")
             return {'CANCELLED'}
        return {"FINISHED"}

class SNA_OT_DeleteMaterialOverride(bpy.types.Operator):
    """Deletes the active object's SD Material Override modifier."""
    bl_idname = "sna.delete_material_override"
    bl_label = "Delete Material Override"
    bl_description = "Deletes Active Object's SD Material Overrides (Modifier, Attribute, Extremes Obj)"
    bl_options = {"REGISTER", "UNDO"}

    modifier_name: bpy.props.StringProperty(name="Modifier Name")

    @classmethod
    def poll(cls, context):
        return context.active_object and hasattr(context.active_object, 'modifiers')

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            return {'CANCELLED'}

        if self.modifier_name not in active_obj.modifiers:
             return {'CANCELLED'}

        remove_modifier(active_obj, self.modifier_name)

        attr_name = f"{active_obj.name}_{self.modifier_name}"
        remove_mesh_attribute(active_obj, attr_name)

        cleanup_associated_data(active_obj.name, MOD_EXTREMES)
        cleanup_unused_sd_data()

        return {"FINISHED"}

class SNA_OT_RemoveAllDiagnostics(bpy.types.Operator):
    """Removes ALL Surface Diagnostics elements from the scene"""
    bl_idname = "sna.remove_all_diagnostics"
    bl_label = "Delete All Diagnostics"
    bl_description = "Removes ALL SD Modifiers, Attributes, Graph Objects, and Empties"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        self.report({'INFO'}, "Removing all Surface Diagnostics elements...")

        objects_to_remove = []
        meshes_to_check = set()
        attributes_to_remove = {} # {obj_name: [attr_name]}
        modifiers_to_remove = {} # {obj_name: [mod_name]}

        # Pass 1: Identification
        for obj in bpy.data.objects:
            obj_name = obj.name
            if SD_PREFIX in obj_name:
                objects_to_remove.append(obj)
                if obj.data and hasattr(obj.data, 'name'):
                    meshes_to_check.add(obj.data.name)

            if hasattr(obj, 'modifiers'):
                for mod in obj.modifiers:
                     if SD_PREFIX in mod.name:
                         if obj_name not in modifiers_to_remove: modifiers_to_remove[obj_name] = []
                         modifiers_to_remove[obj_name].append(mod.name)

                         attr_pattern = f"{obj_name}_{mod.name}"
                         if obj_name not in attributes_to_remove: attributes_to_remove[obj_name] = []
                         attributes_to_remove[obj_name].append(attr_pattern)

            if obj.type == 'MESH' and obj.data and hasattr(obj.data, 'attributes'):
                 for attr in obj.data.attributes:
                      if SD_PREFIX in attr.name:
                            if obj_name not in attributes_to_remove: attributes_to_remove[obj_name] = []
                            attributes_to_remove[obj_name].append(attr.name)

        # Pass 2: Removal
        for obj_name, mod_list in modifiers_to_remove.items():
            obj = bpy.data.objects.get(obj_name)
            if obj:
                 for mod_name in reversed(mod_list):
                     remove_modifier(obj, mod_name)

        for obj_name, attr_list in attributes_to_remove.items():
            obj = bpy.data.objects.get(obj_name)
            if obj:
                for attr_name in set(attr_list):
                    remove_mesh_attribute(obj, attr_name)

        for obj in objects_to_remove:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception: pass

        # Pass 3: Data block cleanup
        for mesh_name in meshes_to_check:
            mesh_data = bpy.data.meshes.get(mesh_name)
            if mesh_data and mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)

        cleanup_unused_sd_data()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

class SNA_OT_ModifyAttributeSelection(bpy.types.Operator):
    """Adds or removes the current Edit Mode selection from an existing SD attribute"""
    bl_idname = "sna.modify_attribute_selection"
    bl_label = "Add / Remove selection"
    bl_description = "Add or Subtract current selection for this diagnostic attribute"
    bl_options = {"REGISTER", "UNDO"}

    add_selection: bpy.props.BoolProperty(name="Add Selection")
    target_object_name: bpy.props.StringProperty(name="Target Object Name")
    attribute_name: bpy.props.StringProperty(name="Attribute Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        target_obj = bpy.data.objects.get(self.target_object_name)
        if not target_obj or not target_obj.data or target_obj.mode != 'EDIT' or target_obj.type != 'MESH':
            return {'CANCELLED'}

        if self.attribute_name not in target_obj.data.attributes:
             return {'CANCELLED'}

        attribute = target_obj.data.attributes[self.attribute_name]
        domain = attribute.domain
        if attribute.data_type != 'INT' or domain not in {'EDGE', 'FACE'}:
             return {'CANCELLED'}

        value_to_set = 1 if self.add_selection else 0
        updated = False

        bm = get_edit_bmesh(target_obj)
        if not bm: return {'CANCELLED'}

        try:
            layer = None
            elements = None
            if domain == 'EDGE':
                layer = bm.edges.layers.int.get(self.attribute_name)
                elements = bm.edges
            elif domain == 'FACE':
                layer = bm.faces.layers.int.get(self.attribute_name)
                elements = bm.faces

            if elements and layer:
                for elem in elements:
                    if elem.select and elem[layer] != value_to_set:
                        elem[layer] = value_to_set
                        updated = True

            if updated:
                 bmesh.update_edit_mesh(target_obj.data)
        except Exception as e:
             self.report({'ERROR'}, f"Error modifying attribute: {e}")
             updated = False

        return {"FINISHED"} if updated else {'CANCELLED'}

class SNA_OT_CreateGeometrySections(bpy.types.Operator):
    """Creates a new object showing geometry sections based on faces"""
    bl_idname = "sna.create_geometry_sections"
    bl_label = "Geometry Sections"
    bl_description = "Creates new object with GN modifier for geometry sections"
    bl_options = {"REGISTER", "UNDO"}

    node_group_name: bpy.props.StringProperty(name="Node Group Name", default=MOD_SECTIONS_GEOM)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.data and obj.type == 'MESH'):
            return False

        if context.mode == 'OBJECT':
            return obj.select_get()
        elif context.mode == 'EDIT_MESH':
            return True
        
        return False

    def execute(self, context):
        mod_type_name = self.node_group_name
        input_id_for_attribute = '3'
        input_id_for_source_obj = '2'
        socket_id_for_ref_obj = '14'

        node_group = get_or_append_asset("node_groups", mod_type_name)
        if not node_group:
            return {'CANCELLED'}

        if context.mode == 'OBJECT':
             target_objects = [o for o in context.selected_editable_objects if o.type == 'MESH']
        elif context.mode == 'EDIT_MESH':
             active_obj = context.active_object
             target_objects = [active_obj] if active_obj and active_obj.type == 'MESH' else []
        else:
             target_objects = []

        if not target_objects:
             return {'CANCELLED'}

        shared_empty = get_or_create_shared_sections_empty(context)
        processed_count = 0
        for source_obj in target_objects:
            use_selection = (context.mode == 'EDIT_MESH' and
                             source_obj.data and hasattr(source_obj.data, 'total_face_sel') and source_obj.data.total_face_sel > 0)

            if use_selection:
                attr_name = create_graph_attribute_from_selection(context, source_obj, mod_type_name, domain='FACE')
                if not attr_name: continue

                modifier, graph_ob = create_graph_object_and_modifier(context, attr_name, mod_type_name)
                if not modifier or not graph_ob:
                    remove_mesh_attribute(source_obj, attr_name)
                    continue

                graph_ob.color = source_obj.color

                source_input_key = f'Input_{input_id_for_source_obj}' if f'Input_{input_id_for_source_obj}' in modifier else f'Socket_{input_id_for_source_obj}'
                setup_gn_modifier_inputs(modifier, {source_input_key: source_obj})
                assign_attribute_to_modifier_input(modifier, input_id_for_attribute, attr_name)

                try:
                    modifier[f'Socket_{socket_id_for_ref_obj}'] = shared_empty
                except (TypeError, KeyError): pass

                processed_count += 1

            else:
                 # Object Mode
                 graph_base_name = f"{source_obj.name}_{mod_type_name}"
                 modifier, graph_ob = create_graph_object_and_modifier(context, graph_base_name, mod_type_name)
                 if not modifier: continue

                 graph_ob.color = source_obj.color

                 attr_name = graph_ob.name
                 if attr_name not in source_obj.data.attributes:
                     source_obj.data.attributes.new(name=attr_name, type='INT', domain='FACE')

                 source_input_key = f'Input_{input_id_for_source_obj}' if f'Input_{input_id_for_source_obj}' in modifier else f'Socket_{input_id_for_source_obj}'
                 inputs_to_set = {source_input_key: source_obj}

                 use_attr_prop_input = f"Input_{input_id_for_attribute}_use_attribute"
                 use_attr_prop_socket = f"Socket_{input_id_for_attribute}_use_attribute"

                 if use_attr_prop_input in modifier:
                       inputs_to_set[use_attr_prop_input] = False
                 elif use_attr_prop_socket in modifier:
                        inputs_to_set[use_attr_prop_socket] = False

                 setup_gn_modifier_inputs(modifier, inputs_to_set)

                 try:
                    modifier[f'Socket_{socket_id_for_ref_obj}'] = shared_empty
                 except (TypeError, KeyError): pass

                 processed_count += 1

        if processed_count == 0:
             return {'CANCELLED'}

        return {"FINISHED"}

class SNA_OT_CreateSectionsCutGeometry(bpy.types.Operator):
    """Applies a geometry node modifier to the object to cut it with sections"""
    bl_idname = "sna.create_sections_cut_geometry"
    bl_label = "Geometry Cut"
    bl_description = "Applies a GN modifier to the object for sections visualization"
    bl_options = {"REGISTER", "UNDO"}

    node_group_name: bpy.props.StringProperty(name="Node Group Name", default=MOD_SECTIONS_CUT_GEOM)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.data):
            return False

        if context.mode == 'OBJECT':
            return obj.select_get() and obj.type in {'MESH', 'CURVE'}
        elif context.mode == 'EDIT_MESH':
            # Operator works on the whole mesh, so it's fine to enable
            # without a sub-component selection.
            return obj.type == 'MESH'
        
        return False

    def execute(self, context):
        mod_type_name = self.node_group_name

        node_group = get_or_append_asset("node_groups", mod_type_name)
        if not node_group:
            return {'CANCELLED'}

        if context.mode == 'EDIT_MESH':
            target_objects = [context.active_object] if context.active_object else []
        else: # Object Mode
            target_objects = [o for o in context.selected_editable_objects if o.type in {'MESH', 'CURVE'}]

        if not target_objects:
             return {'CANCELLED'}

        shared_empty = get_or_create_shared_sections_empty(context)
        processed_count = 0
        for source_obj in target_objects:
            mod_name = mod_type_name
            remove_modifier(source_obj, mod_name)
            modifier = add_geometry_nodes_modifier(source_obj, mod_name, mod_type_name)
            if not modifier: continue

            try:
                modifier['Socket_2'] = shared_empty
            except (TypeError, KeyError): pass

            processed_count += 1

        return {"FINISHED"}

class SNA_OT_CopySectionSettings(bpy.types.Operator):
    """Synchronizes socket values from a source modifier to all other compatible section modifiers"""
    bl_idname = "sna.copy_section_settings"
    bl_label = "Synchronize"
    bl_description = "Copies all socket values from this modifier to all other compatible section modifiers"
    bl_options = {"REGISTER", "UNDO"}

    source_mod_holder_name: bpy.props.StringProperty()
    source_mod_name: bpy.props.StringProperty()

    def execute(self, context):
        source_obj = bpy.data.objects.get(self.source_mod_holder_name)
        if not source_obj: return {'CANCELLED'}

        source_mod = source_obj.modifiers.get(self.source_mod_name)
        if not source_mod or not source_mod.node_group: return {'CANCELLED'}

        source_group_name = source_mod.node_group.name
        if source_group_name not in {MOD_SECTIONS_GEOM, MOD_SECTIONS_CUT_GEOM}:
            return {'CANCELLED'}

        copied_count = 0
        exclude_sockets = ["Socket_2", "Input_2"]

        for obj in context.scene.objects:
            if hasattr(obj, 'modifiers'):
                for target_mod in obj.modifiers:
                    if obj == source_obj and target_mod.name == source_mod.name:
                        continue

                    if target_mod.type == 'NODES' and target_mod.node_group and target_mod.node_group.name == source_group_name:
                        if SD_PREFIX in source_obj.name and SD_PREFIX in obj.name:
                            if obj.show_in_front != source_obj.show_in_front:
                                obj.show_in_front = source_obj.show_in_front

                        for socket in source_mod.node_group.interface.items_tree:
                            if socket.in_out != 'INPUT': continue
                            socket_id = socket.identifier

                            if socket_id in exclude_sockets: continue

                            if socket_id in ["Socket_3", "Input_3"]:
                                try:
                                    s_use_attr = source_mod.get(f"{socket_id}_use_attribute", False)
                                    t_use_attr = target_mod.get(f"{socket_id}_use_attribute", False)
                                    if s_use_attr or t_use_attr: continue
                                except (KeyError, TypeError): continue

                            if socket_id in source_mod and socket_id in target_mod:
                                try:
                                    target_mod[socket_id] = source_mod[socket_id]
                                except (TypeError, KeyError, AttributeError): pass

                        obj.update_tag()
                        copied_count += 1

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {"FINISHED"}

class SNA_OT_ToggleItemVisibility(bpy.types.Operator):
    """Toggles the viewport visibility of a specific diagnostic object or modifier"""
    bl_idname = "sna.toggle_item_visibility"
    bl_label = "Toggle Item Visibility"
    bl_description = "Toggles the viewport visibility of a specific item"
    bl_options = {"REGISTER", "UNDO"}

    object_name: bpy.props.StringProperty(name="Object Name")
    modifier_name: bpy.props.StringProperty(name="Modifier Name", default="")

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if not obj:
            return {'CANCELLED'}

        if self.modifier_name:
            if self.modifier_name in obj.modifiers:
                mod = obj.modifiers[self.modifier_name]
                new_vis = not mod.show_viewport
                mod.show_viewport = new_vis
                mod.show_render = new_vis

                # If this is a material override, check for associated helper objects
                if mod.name == MOD_MAT_OVERRIDE and mod.node_group:
                    node_group_name = mod.node_group.name
                    
                    # Handle Extremes helper for Proximity and Radius
                    if node_group_name in {MOD_PROXIMITY, MOD_MINMAX_RADIUS}:
                        extremes_obj_name = f"{obj.name}_{MOD_EXTREMES}"
                        extremes_obj = bpy.data.objects.get(extremes_obj_name)
                        if extremes_obj:
                            extremes_obj.hide_viewport = not new_vis
                            extremes_obj.hide_render = not new_vis
        else:
            # This is for graph objects (CGraph, AngleGraph, SectionsGeom)
            new_hide_state = not obj.hide_viewport
            obj.hide_viewport = new_hide_state
            obj.hide_render = new_hide_state

        return {"FINISHED"}

class SNA_OT_EmptyOperationPlaceholder(bpy.types.Operator):
    """Placeholder for operations that are conditionally disabled"""
    bl_idname = "sna.empty_op_placeholder"
    bl_label = "Operation Unavailable"
    bl_description = "This operation requires different conditions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    message: bpy.props.StringProperty(default="Operation requires different conditions.")

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'CANCELLED'}


# --- UI Panel ---

class SNA_PT_SurfaceDiagnosticsPanel(bpy.types.Panel):
    bl_label = 'SurfAce Diagnostics'
    bl_idname = 'SNA_PT_SurfaceDiagnosticsPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Surf Ace'
    bl_order = 1

    # --- UI Drawing Helper Methods ---

    def _draw_section_header(self, layout, obj, title, delete_op=None, delete_kwargs=None, vis_prop=None, sync_op=None, sync_kwargs=None):
        """
        Draws a standardized collapsible header with optional tools.
        Returns (is_expanded, box)
        """
        box = layout.box()
        row = box.row(align=True)

        is_expanded = getattr(obj, "show_expanded", True)
        row.prop(obj, "show_expanded", text=title, icon='TRIA_DOWN' if is_expanded else 'TRIA_RIGHT', emboss=False)

        if delete_op:
            op = row.operator(delete_op, text="", icon='PANEL_CLOSE')
            if delete_kwargs:
                for k, v in delete_kwargs.items():
                    setattr(op, k, v)

        if vis_prop:
            target, prop = vis_prop
            is_visible = getattr(target, prop)
            icon = 'HIDE_OFF'
            if "hide_" in prop:
                icon = 'HIDE_OFF' if not is_visible else 'HIDE_ON'
            elif "show_" in prop:
                icon = 'HIDE_OFF' if is_visible else 'HIDE_ON'

            op_vis = row.operator(SNA_OT_ToggleItemVisibility.bl_idname, text="", icon=icon)
            if isinstance(target, bpy.types.Modifier):
                op_vis.object_name = target.id_data.name
                op_vis.modifier_name = target.name
            elif isinstance(target, bpy.types.Object):
                op_vis.object_name = target.name

        if sync_op:
            op_sync = row.operator(sync_op, text="", icon='FILE_REFRESH')
            if sync_kwargs:
                for k, v in sync_kwargs.items():
                    setattr(op_sync, k, v)
        else:
            row.separator(factor=0.2)

        return is_expanded, box

    def _draw_modifier_property(self, layout, modifier, input_id, label, toggle=False, slider=False, icon='NONE', emboss=True, expand=False):
        if not modifier or modifier.type != 'NODES': return

        input_key_input = f"Input_{input_id}"
        input_key_socket = f"Socket_{input_id}"
        input_key_direct = str(input_id)

        prop_key_to_use = None
        if input_key_input in modifier:
            prop_key_to_use = input_key_input
        elif input_key_socket in modifier:
            prop_key_to_use = input_key_socket
        elif input_key_direct in modifier:
             prop_key_to_use = input_key_direct

        if prop_key_to_use:
             try:
                layout.prop(modifier, f'["{prop_key_to_use}"]', text=label, toggle=toggle, slider=slider, icon=icon, emboss=emboss, expand=expand)
             except TypeError:
                 layout.label(text=f"{label}: (Error)")

    def _draw_material_node_inputs(self, layout, material, group_node_name):
        if not material or not material.use_nodes or not material.node_tree:
            return

        node = material.node_tree.nodes.get(group_node_name)
        if not node or node.type != 'GROUP' or not node.inputs:
             return

        layout.separator(factor=0.5)
        for input_socket in node.inputs:
            if input_socket.bl_idname in ['NodeSocketVector', 'NodeSocketShader', 'NodeSocketMaterial', 'NodeSocketGeometry'] or \
               input_socket.name in ['Coordinates', 'Vector']:
                continue

            try:
                 if input_socket.bl_idname == 'NodeSocketBool':
                     layout.prop(input_socket, 'default_value', text=input_socket.name, toggle=True)
                 else:
                     layout.prop(input_socket, 'default_value', text=input_socket.name)
            except Exception:
                 pass
        layout.separator(factor=0.5)

    def _draw_gn_modifier_inputs(self, layout, modifier):
        if not modifier or not modifier.node_group: return

        mod_group_name = modifier.node_group.name
        obj = modifier.id_data

        if mod_group_name == MOD_CURVATURE:
            self._draw_modifier_property(layout, modifier, '0', "Type")
            self._draw_modifier_property(layout, modifier, '34', "Scale")
            self._draw_modifier_property(layout, modifier, '39', "Bands", toggle=True)
        elif mod_group_name == MOD_MINMAX_RADIUS:
            col = layout.column(align=True)
            row = col.row(align=True)
            self._draw_modifier_property(row, modifier, '35', "Min / Max", expand=True)
            self._draw_modifier_property(layout, modifier, '34', "Radius")
            self._draw_modifier_property(layout, modifier, '43', "Show Values", toggle=True)
            if modifier.get("Input_43", False):
                self._draw_extremes_settings(layout, obj)
        elif mod_group_name == MOD_PROXIMITY:
            self._draw_modifier_property(layout, modifier, '44', "Target", icon='OBJECT_DATAMODE')
            self._draw_modifier_property(layout, modifier, '35', "Tolerance")
            self._draw_modifier_property(layout, modifier, '34', "Gradient Scale")
            self._draw_modifier_property(layout, modifier, '43', "Absolute Scale", toggle=True)
            self._draw_modifier_property(layout, modifier, '45', "Show Values", toggle=True)
            if modifier.get("Input_45", False):
                 self._draw_extremes_settings(layout, obj)
        elif mod_group_name == MOD_DRAFT_ANGLE:
            self._draw_modifier_property(layout, modifier, '39', "", icon='OBJECT_DATAMODE')
            self._draw_modifier_property(layout, modifier, '35', "Positive Angle")
            self._draw_modifier_property(layout, modifier, '34', "Negative Angle")
            layout.separator(factor=0.5)
            self._draw_modifier_property(layout, modifier, '41', "Draft Vector", icon='OBJECT_DATAMODE')

    def _draw_extremes_settings(self, layout, source_obj):
         if not source_obj: return
         extremes_obj_name = f"{source_obj.name}_{MOD_EXTREMES}"
         extremes_obj = bpy.data.objects.get(extremes_obj_name)
         extremes_mod = None
         if extremes_obj and hasattr(extremes_obj, 'modifiers') and extremes_obj_name in extremes_obj.modifiers:
              extremes_mod = extremes_obj.modifiers[extremes_obj_name]

         if not extremes_mod:
              return

         layout.separator(factor=0.2)
         self._draw_modifier_property(layout, extremes_mod, '4', "Text Size")
         self._draw_modifier_property(layout, extremes_mod, '6', "Units (mm / m)", toggle=True)
         layout.separator(factor=0.2)

    def _draw_sections_cut_geom_settings(self, layout, modifier):
        col = layout.column(align=True)
        row = col.row(align=True)
        self._draw_modifier_property(row, modifier, '3', "Axis", expand=True)

        self._draw_modifier_property(col, modifier, '13', "Flip", toggle=True)
        self._draw_modifier_property(col, modifier, '14', "Fill Closed", toggle=True)
        if modifier.get("Socket_14", True):
            self._draw_modifier_property(col, modifier, '17', "Fill Material")
            self._draw_modifier_property(col, modifier, '15', "Fill Tolerance")
        self._draw_modifier_property(col, modifier, '9', "CGraph", toggle=True)
        if modifier.get("Socket_9", False):
            self._draw_modifier_property(col, modifier, '6', "Smooth")
            self._draw_modifier_property(col, modifier, '10', "Scale")
            self._draw_modifier_property(col, modifier, '12', "Squash")
            self._draw_modifier_property(col, modifier, '11', "Mute")
        self._draw_modifier_property(col, modifier, '16', "UVMap")

    def _draw_direct_modifier_section(self, layout, context, mod_const, label, settings_func):
        active_obj = context.active_object
        if not active_obj or mod_const not in active_obj.modifiers:
            return

        mod = active_obj.modifiers[mod_const]
        if not mod.node_group: return

        sync_op = "sna.copy_section_settings" if mod_const == MOD_SECTIONS_CUT_GEOM else None
        sync_kwargs = {'source_mod_holder_name': active_obj.name, 'source_mod_name': mod.name} if sync_op else None

        is_expanded, box = self._draw_section_header(
            layout, active_obj, label,
            delete_op=SNA_OT_DeleteMaterialOverride.bl_idname,
            delete_kwargs={'modifier_name': mod.name},
            vis_prop=(mod, "show_viewport"),
            sync_op=sync_op,
            sync_kwargs=sync_kwargs
        )

        if is_expanded:
            col_inner = box.column(align=True)
            col_inner.separator(factor=0.5)
            if settings_func:
                settings_func(col_inner, mod)

            if mod_const == MOD_SECTIONS_CUT_GEOM:
                empty_obj = mod.get("Socket_2")
                if empty_obj and isinstance(empty_obj, bpy.types.Object):
                    col_inner.separator(factor=0.5)
                    col_inner.prop(empty_obj, 'location', text="Location")
                    col_inner.prop(empty_obj, 'rotation_euler', text="Rotation")
                else:
                    col_inner.separator(factor=0.5)
                    col_inner.label(text="No reference empty assigned", icon='INFO')

        layout.separator(factor=0.5)

    def _draw_material_settings_section(self, layout, context, mat_const, label, gn_const, input_socket):
        active_obj = context.active_object
        if not active_obj or MOD_MAT_OVERRIDE not in active_obj.modifiers:
            return

        mod = active_obj.modifiers[MOD_MAT_OVERRIDE]
        mod_group = mod.node_group
        if not mod_group: return

        show_section = False
        material_input = None

        uuid_value = ASSET_UUID_MAP.get("materials", {}).get(mat_const)

        def is_correct_material(mat):
            if not mat or not isinstance(mat, bpy.types.Material): return False
            if uuid_value: return mat.get("SD_UUID") == uuid_value
            else: return mat.name == mat_const

        if mod_group.name == gn_const:
            material_input = mod.get(input_socket, None)
            if is_correct_material(material_input):
                show_section = True
        elif mod_group.name == MOD_MAT_OVERRIDE and gn_const == MOD_MAT_OVERRIDE:
            material_input = mod.get(input_socket, None)
            if is_correct_material(material_input):
                show_section = True

        if show_section:
            is_expanded, box = self._draw_section_header(
                layout, active_obj, label,
                delete_op=SNA_OT_DeleteMaterialOverride.bl_idname,
                delete_kwargs={'modifier_name': mod.name},
                vis_prop=(mod, "show_viewport")
            )

            if is_expanded:
                col_inner = box.column(align=True)

                input_id_for_selection = '37'
                input_prop_name = f'Input_{input_id_for_selection}'
                socket_prop_name = f'Socket_{input_id_for_selection}'
                has_attribute_input_37 = input_prop_name in mod or socket_prop_name in mod

                if has_attribute_input_37 and active_obj.mode == 'EDIT' and active_obj.type == 'MESH':
                    attr_name_standard = f"{active_obj.name}_{MOD_MAT_OVERRIDE}"
                    if hasattr(active_obj.data, 'attributes') and attr_name_standard in active_obj.data.attributes:
                        row_attr = col_inner.row(align=True)
                        op_add = row_attr.operator(SNA_OT_ModifyAttributeSelection.bl_idname, text="", icon='ADD')
                        op_add.add_selection = True
                        op_add.target_object_name = active_obj.name
                        op_add.attribute_name = attr_name_standard

                        op_rem = row_attr.operator(SNA_OT_ModifyAttributeSelection.bl_idname, text="", icon='REMOVE')
                        op_rem.add_selection = False
                        op_rem.target_object_name = active_obj.name
                        op_rem.attribute_name = attr_name_standard

                col_inner.separator(factor=0.5)
                if mod_group.name == MOD_MAT_OVERRIDE:
                     if material_input:
                          if material_input.use_nodes and material_input.node_tree:
                               group_node = next((n for n in material_input.node_tree.nodes if n.type == 'GROUP'), None)
                               if group_node:
                                    if mat_const in {MAT_SECTION_LINES, MAT_SECTION_CUT}:
                                         coord_empty = bpy.data.objects.get(EMPTY_SECTIONS_COORD)
                                         if coord_empty:
                                              col_inner.separator(factor=0.3)
                                              col_inner.prop(coord_empty, 'location', text="Location")
                                              col_inner.prop(coord_empty, 'rotation_euler', text="Rotation")
                                              col_inner.separator(factor=0.3)
                                    self._draw_material_node_inputs(col_inner, material_input, group_node.name)
                elif mod_group.name == gn_const:
                     self._draw_gn_modifier_inputs(col_inner, mod)
            layout.separator(factor=0.5)

    def _draw_graph_settings_section(self, layout, context, graph_type_prefix, label):
         active_obj = context.active_object
         if not active_obj: return

         # --- Case 1: The Active Object IS the Graph Object ---
         is_active_obj_the_graph = (
             active_obj.type == 'MESH' and
             graph_type_prefix in active_obj.name and
             hasattr(active_obj, 'modifiers') and
             active_obj.name in active_obj.modifiers and
             active_obj.modifiers[active_obj.name].node_group and
             active_obj.modifiers[active_obj.name].node_group.name == graph_type_prefix
         )

         if is_active_obj_the_graph:
             mod = active_obj.modifiers[active_obj.name]
             parts = active_obj.name.split(f"_{graph_type_prefix}")
             source_object_name = parts[0] if parts and parts[0] else ""

             sync_op = "sna.copy_section_settings" if graph_type_prefix == MOD_SECTIONS_GEOM else None
             sync_kwargs = {'source_mod_holder_name': active_obj.name, 'source_mod_name': mod.name} if sync_op else None

             is_expanded, box = self._draw_section_header(
                layout, active_obj, label,
                delete_op=SNA_OT_RemoveGraphObject.bl_idname,
                delete_kwargs={
                    'graph_object_name': active_obj.name,
                    'source_object_name': source_object_name,
                    'graph_type': graph_type_prefix
                },
                vis_prop=(active_obj, "hide_viewport"),
                sync_op=sync_op,
                sync_kwargs=sync_kwargs
             )

             if is_expanded:
                 col_inner = box.column(align=True)
                 col_inner.separator(factor=0.3)

                 if graph_type_prefix == MOD_CGRAPH: self._draw_cgraph_settings(col_inner, mod)
                 elif graph_type_prefix == MOD_ANGLEGRAPH: self._draw_anglegraph_settings(col_inner, mod)
                 elif graph_type_prefix == MOD_SECTIONS_GEOM:
                     self._draw_sections_geom_settings(col_inner, mod)
                     col_inner.separator(factor=0.5)
                     if mod.get("Socket_13") == 1 and mod.get("Socket_14"):
                         ref_obj = mod["Socket_14"]
                         col_inner.prop(ref_obj, 'location', text="Location")
                         col_inner.prop(ref_obj, 'rotation_euler', text="Rotation")
                     else:
                         col_inner.prop(active_obj, 'location', text="Location")
                         col_inner.prop(active_obj, 'rotation_euler', text="Rotation")

             layout.separator(factor=0.5)
             return

         # --- Case 2: The Active Object is the Source Object ---
         if active_obj.type == 'MESH' and active_obj.data and hasattr(active_obj.data, 'attributes'):
             found_graphs_for_this_source = []
             for attr in active_obj.data.attributes:
                  if attr.name.startswith(f"{active_obj.name}_{graph_type_prefix}"):
                       graph_obj = bpy.data.objects.get(attr.name)
                       mod = graph_obj.modifiers.get(attr.name) if graph_obj and hasattr(graph_obj, 'modifiers') else None
                       if graph_obj and mod and mod.node_group and mod.node_group.name == graph_type_prefix:
                           found_graphs_for_this_source.append({'graph_obj': graph_obj, 'mod': mod, 'attr_name': attr.name})

             if found_graphs_for_this_source:
                 col_all_graphs = layout.column(align=True)
                 for graph_info in found_graphs_for_this_source:
                     graph_obj = graph_info['graph_obj']
                     mod = graph_info['mod']
                     attr_name = graph_info['attr_name']

                     sync_op = "sna.copy_section_settings" if graph_type_prefix == MOD_SECTIONS_GEOM else None
                     sync_kwargs = {'source_mod_holder_name': graph_obj.name, 'source_mod_name': mod.name} if sync_op else None

                     is_expanded, box = self._draw_section_header(
                        layout, graph_obj, label,
                        delete_op=SNA_OT_RemoveGraphObject.bl_idname,
                        delete_kwargs={
                            'graph_object_name': graph_obj.name,
                            'source_object_name': active_obj.name,
                            'graph_type': graph_type_prefix
                        },
                        vis_prop=(graph_obj, "hide_viewport"),
                        sync_op=sync_op,
                        sync_kwargs=sync_kwargs
                     )

                     if is_expanded:
                         col_inner = box.column(align=True)

                         if active_obj.mode == 'EDIT' and attr_name:
                              row_attr = col_inner.row(align=True)
                              op_add = row_attr.operator(SNA_OT_ModifyAttributeSelection.bl_idname, text="", icon='ADD')
                              op_add.add_selection = True
                              op_add.target_object_name = active_obj.name
                              op_add.attribute_name = attr_name

                              op_rem = row_attr.operator(SNA_OT_ModifyAttributeSelection.bl_idname, text="", icon='REMOVE')
                              op_rem.add_selection = False
                              op_rem.target_object_name = active_obj.name
                              op_rem.attribute_name = attr_name

                         if graph_type_prefix == MOD_CGRAPH: self._draw_cgraph_settings(col_inner, mod)
                         elif graph_type_prefix == MOD_ANGLEGRAPH: self._draw_anglegraph_settings(col_inner, mod)
                         elif graph_type_prefix == MOD_SECTIONS_GEOM:
                             self._draw_sections_geom_settings(col_inner, mod)
                             col_inner.separator(factor=0.5)
                             if mod.get("Socket_13") == 1 and mod.get("Socket_14"):
                                 ref_obj = mod["Socket_14"]
                                 col_inner.prop(ref_obj, 'location', text="Location")
                                 col_inner.prop(ref_obj, 'rotation_euler', text="Rotation")
                             else:
                                 col_inner.prop(graph_obj, 'location', text="Location")
                                 col_inner.prop(graph_obj, 'rotation_euler', text="Rotation")

                     col_all_graphs.separator(factor=0.5)

    def _draw_cgraph_settings(self, layout, modifier):
        col = layout.column(align=True)
        self._draw_modifier_property(col, modifier, '3', "Scale")
        self._draw_modifier_property(col, modifier, '14', "Mute Above")
        self._draw_modifier_property(col, modifier, '22', "Squash")

        row = col.row(align=True)
        self._draw_modifier_property(row, modifier, '0', "Curve Type", expand=True)

        obj = modifier.id_data
        if obj:
            col.prop(obj, 'show_in_front', text='In Front', toggle=True)

        self._draw_modifier_property(col, modifier, '15', "Auto Scale", toggle=True)
        self._draw_modifier_property(col, modifier, '19', "Show Values", toggle=True)

        if modifier.get("Input_19", False):
            self._draw_modifier_property(col, modifier, '21', "Sample Factor")
            self._draw_modifier_property(col, modifier, '17', "Text Size")
            row = col.row(align=True)
            self._draw_modifier_property(row, modifier, '1', "Units (mm / m)", expand=True)

        if obj:
            col.prop(obj, 'color', text="Graph Color")

    def _draw_anglegraph_settings(self, layout, modifier):
        col = layout.column(align=True)
        self._draw_modifier_property(col, modifier, '19', "Auto Scale", toggle=True)
        self._draw_modifier_property(col, modifier, '3', "Scale")

        obj = modifier.id_data
        if obj:
            col.prop(obj, 'show_in_front', text='In Front', toggle=True)

        self._draw_modifier_property(col, modifier, '25', "Show Values", toggle=True)
        if modifier.get("Input_25", False):
            self._draw_modifier_property(col, modifier, '23', "Text Size")
            self._draw_modifier_property(col, modifier, '26', "Sample Factor")

        if obj:
            col.prop(obj, 'color', text="Graph Color")

    def _draw_sections_geom_settings(self, layout, modifier):
        col = layout.column(align=True)
        row = col.row(align=True)
        self._draw_modifier_property(row, modifier, '3', "Axis", expand=True)
        row = col.row(align=True)
        self._draw_modifier_property(row, modifier, '13', "Ref. Obj.", expand=True)

        if modifier.get("Socket_13") == 1:
            self._draw_modifier_property(col, modifier, '14', "")

        row = col.column(align=True)
        self._draw_modifier_property(col, modifier, '7', "Single Section", toggle=True)

        if not modifier.get("Socket_7", False):
            self._draw_modifier_property(col, modifier, '5', "Distance")

        obj = modifier.id_data
        if obj:
            col.prop(obj, 'show_in_front', text='In Front', toggle=True)

        self._draw_modifier_property(col, modifier, '9', "CGraph", toggle=True)
        if modifier.get("Socket_9", True):
            self._draw_modifier_property(col, modifier, '6', "Smooth")
            self._draw_modifier_property(col, modifier, '10', "Scale")
            self._draw_modifier_property(col, modifier, '12', "Squash")
            self._draw_modifier_property(col, modifier, '11', "Mute")
        col.prop(obj, 'color', text="Section Color")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active_obj = context.active_object
        is_condensed = scene.sna_ui_condensed

        # --- Header Row ---
        row = layout.row(align=True)
        row.scale_y = 1.1
        row.operator(SNA_OT_RemoveAllDiagnostics.bl_idname, text="Delete All", icon='CANCEL')

        is_visible = scene.sna_visibility_switch
        icon = 'HIDE_OFF' if is_visible else 'HIDE_ON'
        op = row.operator(SNA_OT_UnhideAllDiagnosticTools.bl_idname, text="", icon=icon)
        op.show = not is_visible


        # --- Main Buttons Grid ---
        col_main = layout.column(align=True)
        col_main.separator(factor=0.5)
        col_main.scale_y = 1.15

        grid = col_main.grid_flow(columns=(5 if is_condensed else 1), row_major=True, even_columns=True, even_rows=True, align=True)

        def add_op_button(op_idname, text, icon_img_name_no_ext, op_props=None):
             icon_id = 0
             if _icons and icon_img_name_no_ext in _icons:
                 icon_id = _icons[icon_img_name_no_ext].icon_id

             op = grid.operator(op_idname, text="" if is_condensed else text, icon_value=icon_id)
             if op_props:
                 for prop, value in op_props.items():
                     setattr(op, prop, value)


        # Material Overrides
        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Zebra", "zebra", {
            'mat_name': MAT_ZEBRA, 'node_group_name': MOD_MAT_OVERRIDE, 'input_socket_name': 'Input_2'})
        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Isoangle", "isoangle", {
            'mat_name': MAT_ISOANGLE, 'node_group_name': MOD_MAT_OVERRIDE, 'input_socket_name': 'Input_2'})

        prefs = bpy.context.preferences.addons[__package__].preferences

        if prefs.legacy_sections_cut:
            add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Sections", "sections", {
                'mat_name': MAT_SECTION_LINES, 'node_group_name': MOD_MAT_OVERRIDE, 'input_socket_name': 'Input_2'})
            add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Cut", "Slice", {
                 'mat_name': MAT_SECTION_CUT, 'node_group_name': MOD_MAT_OVERRIDE, 'input_socket_name': 'Input_2'})
        else:
            can_create_geom_sections = SNA_OT_CreateGeometrySections.poll(context)
            geom_sections_op_id = SNA_OT_CreateGeometrySections.bl_idname if can_create_geom_sections else SNA_OT_EmptyOperationPlaceholder.bl_idname
            add_op_button(geom_sections_op_id, "Sections", "sections")

            can_create_sections_cut = SNA_OT_CreateSectionsCutGeometry.poll(context)
            sections_cut_op_id = SNA_OT_CreateSectionsCutGeometry.bl_idname if can_create_sections_cut else SNA_OT_EmptyOperationPlaceholder.bl_idname
            add_op_button(sections_cut_op_id, "Cut", "Slice")

        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Proximity", "proximity", {
             'mat_name': MAT_PROXIMITY, 'node_group_name': MOD_PROXIMITY, 'input_socket_name': 'Input_40'})
        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Draft", "draft", {
             'mat_name': MAT_DRAFT_ANGLE, 'node_group_name': MOD_DRAFT_ANGLE, 'input_socket_name': 'Input_40'})
        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Radius", "Radius", {
             'mat_name': MAT_MINMAX_RADIUS, 'node_group_name': MOD_MINMAX_RADIUS, 'input_socket_name': 'Input_40'})
        add_op_button(SNA_OT_AddMaterialOverride.bl_idname, "Curvature", "curvature", {
             'mat_name': MAT_CURVATURE, 'node_group_name': MOD_CURVATURE, 'input_socket_name': 'Input_40'})


        can_create_cgraph = SNA_OT_CreateCurvatureGraph.poll(context)
        cgraph_op_id = SNA_OT_CreateCurvatureGraph.bl_idname if can_create_cgraph else SNA_OT_EmptyOperationPlaceholder.bl_idname
        add_op_button(cgraph_op_id, "Curvature Graph", "cgraph")

        can_create_anglegraph = SNA_OT_CreateAngleGraph.poll(context)
        angraph_op_id = SNA_OT_CreateAngleGraph.bl_idname if can_create_anglegraph else SNA_OT_EmptyOperationPlaceholder.bl_idname
        add_op_button(angraph_op_id, "Angle Graph", "AngleGraph")


        col_main.separator(factor=1.5)

        # --- Settings Sections ---
        if active_obj:
             col_settings = layout.column(align=True)

             self._draw_material_settings_section(col_settings, context, MAT_ZEBRA, "Zebra", MOD_MAT_OVERRIDE, 'Input_2')
             self._draw_material_settings_section(col_settings, context, MAT_ISOANGLE, "Isoangle", MOD_MAT_OVERRIDE, 'Input_2')

             if prefs.legacy_sections_cut:
                 self._draw_material_settings_section(col_settings, context, MAT_SECTION_LINES, "Sections", MOD_MAT_OVERRIDE, 'Input_2')
                 self._draw_material_settings_section(col_settings, context, MAT_SECTION_CUT, "Cut", MOD_MAT_OVERRIDE, 'Input_2')
             else:
                 self._draw_graph_settings_section(col_settings, context, MOD_SECTIONS_GEOM, "Sections")
                 self._draw_direct_modifier_section(col_settings, context, MOD_SECTIONS_CUT_GEOM, "Cut", self._draw_sections_cut_geom_settings)

             self._draw_material_settings_section(col_settings, context, MAT_PROXIMITY, "Proximity", MOD_PROXIMITY, 'Input_40')
             self._draw_material_settings_section(col_settings, context, MAT_DRAFT_ANGLE, "Draft", MOD_DRAFT_ANGLE, 'Input_40')
             self._draw_material_settings_section(col_settings, context, MAT_MINMAX_RADIUS, "Radius", MOD_MINMAX_RADIUS, 'Input_40')
             self._draw_material_settings_section(col_settings, context, MAT_CURVATURE, "Curvature", MOD_CURVATURE, 'Input_40')

             self._draw_graph_settings_section(col_settings, context, MOD_CGRAPH, "Curvature Graph")
             self._draw_graph_settings_section(col_settings, context, MOD_ANGLEGRAPH, "Angle Graph")


        # --- Preferences Section ---
        box = layout.box()
        row = box.row()
        row.prop(scene, 'sna_properties', text="", icon='TRIA_DOWN' if scene.sna_properties else 'TRIA_RIGHT', emboss=False)
        row.label(text="Utilities")

        if scene.sna_properties:
             col_prefs = box.column(align=True)
             col_prefs.prop(scene, 'sna_ui_condensed', text="Condensed UI", toggle=True)
             if hasattr(context, "scene") and hasattr(context.scene, "render"):
                  col_prefs.prop(context.scene.render, 'use_high_quality_normals', text="High Quality Normals", toggle=True)
             else: col_prefs.label(text="Render settings unavailable.")
             if active_obj:
                 col_prefs.prop(active_obj, 'color', text="Object Color")


# --- Registration ---

ICONS = {
    'zebra': 'sd_zebra.svg',
    'isoangle': 'sd_isoangle.svg',
    'sections': 'sd_sections.svg',
    'Slice': 'sd_cut.svg',
    'proximity': 'sd_proximity.svg',
    'draft': 'sd_draft.svg',
    'Radius': 'sd_radius.svg',
    'curvature': 'sd_curvature.svg',
    'cgraph': 'sd_cgraph.svg',
    'AngleGraph': 'sd_agraph.svg',
}

classes = [
    SurfaceDiagnosticsAddonPreferences,
    SNA_OT_UnhideAllDiagnosticTools,
    SNA_OT_RemoveGraphObject,
    SNA_OT_AddMaterialOverride,
    SNA_OT_CreateAngleGraph,
    SNA_OT_CreateCurvatureGraph,
    SNA_OT_DeleteMaterialOverride,
    SNA_OT_RemoveAllDiagnostics,
    SNA_OT_ModifyAttributeSelection,
    SNA_OT_CreateGeometrySections,
    SNA_OT_CreateSectionsCutGeometry,
    SNA_OT_CopySectionSettings,
    SNA_OT_ToggleItemVisibility,
    SNA_OT_EmptyOperationPlaceholder,
    SNA_PT_SurfaceDiagnosticsPanel,
]

def register():
    global _icons
    _icons = bpy.utils.previews.new()
    load_icons(ICONS)

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.show_expanded = bpy.props.BoolProperty(name="Show Expanded", default=True)
    bpy.types.Scene.sna_visibility_switch = bpy.props.BoolProperty(
        name="Toggle Diagnostics Visibility",
        description="Global switch for showing/hiding all diagnostic tools",
        default=True
    )
    bpy.types.Scene.sna_ui_condensed = bpy.props.BoolProperty(
        name="Condensed UI",
        description="Use a more compact layout for the main buttons",
        default=True
    )
    bpy.types.Scene.sna_properties = bpy.props.BoolProperty(
        name="SNA Properties",
        description="Expand or collapse the main properties section",
        default=True
    )


def unregister():
    global _icons
    if _icons:
        bpy.utils.previews.remove(_icons)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.show_expanded
    del bpy.types.Scene.sna_visibility_switch
    del bpy.types.Scene.sna_ui_condensed
    del bpy.types.Scene.sna_properties

# --- END OF FILE __init__.py ---