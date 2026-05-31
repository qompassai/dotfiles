bl_info = {
    "name": "Dynamic Head Property Manager",
    "author": "Cloud Guy",
    "version": (1, 0, 7),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > FACS",
    "description": "Manage custom facial properties for Roblox Bundles",
    "category": "Animation",
}

import bpy
import re
import difflib
import os
import json
from bpy.app.handlers import persistent
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, EnumProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel

FACS_NEW_ALL_ORDER = [
    "Neutral",
    "LeftEyeClosed", "RightEyeClosed", "EyesLookDown", "JawDrop", "Pucker",
    "LeftLipCornerPuller", "RightLipCornerPuller", "ChinRaiser", "ChinRaiserUpperLip",
    "LeftCheekRaiser", "RightCheekRaiser", "LeftInnerBrowRaiser", "RightInnerBrowRaiser",
    "LeftLipCornerDown", "RightLipCornerDown", "LeftLowerLipDepressor", "RightLowerLipDepressor",
    "EyesLookLeft", "EyesLookRight", "EyesLookUp",
    "LeftLipStretcher", "LeftUpperLipRaiser", "LipsTogether",
    "RightLipStretcher", "RightUpperLipRaiser",
    "FlatPucker", "Funneler", "LowerLipSuck", "LipPresser",
    "MouthLeft", "MouthRight", "UpperLipSuck",
    "LeftCheekPuff", "LeftDimpler", "RightCheekPuff", "RightDimpler",
    "JawLeft", "JawRight",
    "Corrugator", "LeftBrowLowerer", "LeftOuterBrowRaiser", "LeftNoseWrinkler",
    "RightBrowLowerer", "RightOuterBrowRaiser", "RightNoseWrinkler",
    "LeftEyeUpperLidRaiser", "RightEyeUpperLidRaiser",
    "TongueDown", "TongueOut", "TongueUp"
]

FACS_NEW_PRESET_CATEGORIES = {
    "All": FACS_NEW_ALL_ORDER,
    "Required": [
        "Neutral", "LeftEyeClosed", "RightEyeClosed", "EyesLookDown", "JawDrop",
        "Pucker", "LeftLipCornerPuller", "RightLipCornerPuller", "ChinRaiser",
        "ChinRaiserUpperLip", "LeftCheekRaiser", "RightCheekRaiser",
        "LeftInnerBrowRaiser", "RightInnerBrowRaiser", "LeftLipCornerDown",
        "RightLipCornerDown", "LeftLowerLipDepressor", "RightLowerLipDepressor"
    ],
    "Mouth": [
        "LeftLipStretcher", "LeftUpperLipRaiser", "LipsTogether",
        "RightLipStretcher", "RightUpperLipRaiser", "FlatPucker", "Funneler",
        "LowerLipSuck", "LipPresser", "MouthLeft", "MouthRight", "UpperLipSuck",
        "LeftDimpler", "RightDimpler", "JawLeft", "JawRight"
    ],
    "Cheeks": [
        "LeftCheekPuff", "RightCheekPuff"
    ],
    "Brows": [
        "Corrugator", "LeftBrowLowerer", "LeftOuterBrowRaiser",
        "RightBrowLowerer", "RightOuterBrowRaiser"
    ],
    "Eyes": [
        "EyesLookLeft", "EyesLookRight", "EyesLookUp",
        "LeftEyeUpperLidRaiser", "RightEyeUpperLidRaiser"
    ],
    "Nose": [
        "LeftNoseWrinkler", "RightNoseWrinkler"
    ],
    "Tongue": [
        "TongueDown", "TongueOut", "TongueUp"
    ]
}

FACS_OLD_PRESET_CATEGORIES = {
    "Required": [
        "Neutral", "EyesLookDown", "EyesLookLeft", "EyesLookRight", "EyesLookUp",
        "JawDrop", "LeftEyeClosed", "LeftLipCornerPuller", "LeftLipStretcher",
        "LeftLowerLipDepressor", "LeftUpperLipRaiser", "LipsTogether", "Pucker",
        "RightEyeClosed", "RightLipCornerPuller", "RightLipStretcher",
        "RightLowerLipDepressor", "RightUpperLipRaiser"
    ],
    "Mouth": [
        "ChinRaiser", "ChinRaiserUpperLip", "FlatPucker", "Funneler", "JawLeft",
        "JawRight", "LeftDimpler", "LeftLipCornerDown", "LipPresser", "LowerLipSuck",
        "MouthLeft", "MouthRight", "RightDimpler", "RightLipCornerDown", "UpperLipSuck"
    ],
    "Cheeks": [
        "LeftCheekPuff", "LeftCheekRaiser", "RightCheekPuff", "RightCheekRaiser"
    ],
    "Brows": [
        "Corrugator", "LeftBrowLowerer", "LeftInnerBrowRaiser", "LeftOuterBrowRaiser",
        "RightBrowLowerer", "RightInnerBrowRaiser", "RightOuterBrowRaiser"
    ],
    "Eyes": [
        "LeftEyeUpperLidRaiser", "RightEyeUpperLidRaiser"
    ],
    "Nose": [
        "LeftNoseWrinkler", "RightNoseWrinkler"
    ],
    "Tongue": [
        "TongueDown", "TongueOut", "TongueUp"
    ]
}

FACS_ORDER_ITEMS = (
    ('NEW', "New (v1.0.7)", "Use the current FACS order used by this version"),
    ('OLD', "Old (v1.0.4)", "Use the legacy FACS order from v1.0.4")
)

FACS_ORDER_WARNING_LINES = (
    "As of 6/3/2026:",
    'Only the "New" one works.',
    "DD/MM/YY"
)
FIRST_RUN_SETTINGS_MARKER = "facs_settings_seen_v1_0_6.flag"
FIRST_RUN_POPUP_MAX_ATTEMPTS = 20
_first_run_popup_attempts = 0


def build_expression_order(categories):
    ordered = []
    seen = set()
    for expressions in categories.values():
        for expr in expressions:
            if expr not in seen:
                seen.add(expr)
                ordered.append(expr)
    return ordered


FACS_OLD_ALL_ORDER = build_expression_order(FACS_OLD_PRESET_CATEGORIES)
FACS_OLD_PRESET_CATEGORIES = {"All": list(FACS_OLD_ALL_ORDER), **FACS_OLD_PRESET_CATEGORIES}
FACS_ALL_CATEGORY_NAMES = list(
    dict.fromkeys(list(FACS_NEW_PRESET_CATEGORIES.keys()) + list(FACS_OLD_PRESET_CATEGORIES.keys()))
)


def get_facs_order_label(order_mode):
    return "Old (v1.0.4)" if order_mode == 'OLD' else "New (v1.0.7)"


def get_preset_categories(order_mode='NEW'):
    if order_mode == 'OLD':
        return FACS_OLD_PRESET_CATEGORIES
    return FACS_NEW_PRESET_CATEGORIES


def get_active_order_mode(context):
    try:
        order_mode = context.scene.facs_main.props.facs_order_mode
        if order_mode in {'NEW', 'OLD'}:
            return order_mode
        return 'NEW'
    except Exception:
        return 'NEW'


def get_active_preset_categories(context, override_mode=None):
    order_mode = override_mode if override_mode is not None else get_active_order_mode(context)
    return get_preset_categories(order_mode)


def get_active_all_expressions(context, override_mode=None):
    order_mode = override_mode if override_mode is not None else get_active_order_mode(context)
    if order_mode == 'OLD':
        return list(FACS_OLD_ALL_ORDER)
    return list(FACS_NEW_ALL_ORDER)


def draw_order_warning(layout):
    warning_box = layout.box()
    warning_box.alert = True
    for i, warning_line in enumerate(FACS_ORDER_WARNING_LINES):
        if i == 0:
            warning_box.label(text=warning_line, icon='ERROR')
        else:
            warning_box.label(text=warning_line)


def get_first_run_marker_path():
    try:
        user_dir = bpy.utils.extension_path_user(__package__, create=True)
    except Exception:
        return ""
    return os.path.join(user_dir, FIRST_RUN_SETTINGS_MARKER)


def has_seen_first_run_settings():
    marker_path = get_first_run_marker_path()
    if not marker_path:
        return True
    return os.path.exists(marker_path)


def mark_first_run_settings_seen():
    marker_path = get_first_run_marker_path()
    if not marker_path:
        return
    try:
        with open(marker_path, 'w', encoding='utf-8') as f:
            f.write("seen")
    except Exception as e:
        print(f"Error saving first-run marker: {str(e)}")


def show_first_run_settings_popup():
    global _first_run_popup_attempts
    _first_run_popup_attempts += 1

    if has_seen_first_run_settings():
        return None

    wm = getattr(bpy.context, "window_manager", None)
    if wm is None or len(wm.windows) == 0:
        if _first_run_popup_attempts < FIRST_RUN_POPUP_MAX_ATTEMPTS:
            return 0.75
        mark_first_run_settings_seen()
        return None

    try:
        for window in wm.windows:
            screen = window.screen
            if screen is None:
                continue

            for area in screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region is None:
                    continue

                with bpy.context.temp_override(window=window, screen=screen, area=area, region=region):
                    bpy.ops.object.facs_open_settings('INVOKE_DEFAULT')

                mark_first_run_settings_seen()
                return None
    except Exception as e:
        print(f"Error opening first-run settings popup: {str(e)}")

    if _first_run_popup_attempts < FIRST_RUN_POPUP_MAX_ATTEMPTS:
        return 0.75
    mark_first_run_settings_seen()
    return None

FILTERED_EXPRESSIONS_CACHE = {}

def force_ui_update():
    """Force update all UI areas in all screens to ensure changes are visible"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()

def get_target_object_in_active_scene(context, target_name):
    """Resolve target object strictly from the active scene."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    clean_name = (target_name or "").strip()
    if not clean_name:
        return None
    return scene.objects.get(clean_name)

def get_saved_expression_list(main, list_name):
    """Find a saved expression list by name."""
    if not list_name:
        return None
    for saved in main.saved_expression_lists:
        if saved.name == list_name:
            return saved
    return None

def find_favorite_by_name_or_link(main, list_name):
    """Find favorite item by display name or internal linked name."""
    if not list_name:
        return None
    for favorite in main.favorite_lists:
        if favorite.name == list_name or favorite.linked_name == list_name:
            return favorite
    return None

def favorite_name_update(self, context):
    """Keep favorite display name and saved payload linked when renaming."""
    if context is None or context.scene is None or not hasattr(context.scene, "facs_main"):
        return

    main = context.scene.facs_main
    old_name = (self.linked_name or "").strip()
    new_name = (self.name or "").strip()

    if not new_name:
        if old_name and self.name != old_name:
            self.name = old_name
        return

    if not old_name:
        self.linked_name = new_name
        return

    if new_name == old_name:
        return

    for favorite in main.favorite_lists:
        if favorite.as_pointer() != self.as_pointer() and favorite.name == new_name:
            self.name = old_name
            return

    saved_data = get_saved_expression_list(main, old_name)
    if saved_data:
        saved_data.name = new_name

    self.linked_name = new_name
    save_favorites_to_json(context)
    force_ui_update()

def add_to_last_used(context, expression_name):
    last_used = []
    for item in context.scene.facs_main.last_used_expressions:
        last_used.append(item.name)
    
    if expression_name in last_used:
        index = last_used.index(expression_name)
        context.scene.facs_main.last_used_expressions.remove(index)
    
    item = context.scene.facs_main.last_used_expressions.add()
    item.name = expression_name
    context.scene.facs_main.last_used_expressions.move(len(context.scene.facs_main.last_used_expressions)-1, 0)
    
    while len(context.scene.facs_main.last_used_expressions) > 10:
        context.scene.facs_main.last_used_expressions.remove(10)

def improved_search_filter(filter_text, expressions):
    global FILTERED_EXPRESSIONS_CACHE
    
    filter_text = filter_text.lower().strip()
    if not filter_text:
        return expressions
    
    cache_key = filter_text
    if cache_key in FILTERED_EXPRESSIONS_CACHE:
        return FILTERED_EXPRESSIONS_CACHE[cache_key]
    
    exact_matches = [expr for expr in expressions if filter_text in expr.lower()]
    
    if exact_matches:
        FILTERED_EXPRESSIONS_CACHE[cache_key] = exact_matches
        return exact_matches
    
    if len(filter_text) <= 2:
        prefix_matches = [expr for expr in expressions if expr.lower().startswith(filter_text)]
        if prefix_matches:
            FILTERED_EXPRESSIONS_CACHE[cache_key] = prefix_matches
            return prefix_matches
    
    possible_matches = [expr for expr in expressions if any(c in expr.lower() for c in filter_text)]
    
    scored_matches = [(expr, difflib.SequenceMatcher(None, filter_text, expr.lower()).ratio()) 
                      for expr in possible_matches]
    
    filtered_exprs = [expr for expr, score in scored_matches if score > 0.3]
    
    filtered_exprs.sort(key=lambda expr: difflib.SequenceMatcher(None, filter_text, expr.lower()).ratio(), reverse=True)
    
    FILTERED_EXPRESSIONS_CACHE[cache_key] = filtered_exprs
    return filtered_exprs

class FACS_ExpressionItem(PropertyGroup):
    expression: StringProperty(
        name="Expression",
        description="Name of the FACS expression",
        default=""
    )
    frame: IntProperty(
        name="Frame",
        description="Frame number for this expression",
        default=0,
        min=0,
        subtype='NONE'
    )

class FACS_FavoriteListItem(PropertyGroup):
    """Favorite expression list item"""
    name: StringProperty(
        name="Name",
        description="Name of this favorite expression list",
        default="Unnamed",
        update=favorite_name_update
    )
    
    description: StringProperty(
        name="Description",
        description="Description of this favorite expression list",
        default=""
    )

    linked_name: StringProperty(
        name="Linked Name",
        description="Internal key used to keep this favorite linked to saved payload",
        default="",
        options={'HIDDEN'}
    )

def save_favorites_to_json(context):
    """Save favorite expression lists to a JSON file in the addon's user directory"""
    try:
        user_dir = bpy.utils.extension_path_user(__package__, create=True)
        
        favorites_path = os.path.join(user_dir, "favorites.json")
        
        favorites = []
        for item in context.scene.facs_main.favorite_lists:
            key_name = item.linked_name if item.linked_name else item.name
            saved_data = (
                get_saved_expression_list(context.scene.facs_main, key_name) or
                get_saved_expression_list(context.scene.facs_main, item.name)
            )

            if not saved_data or not saved_data.expressions:
                continue

            if saved_data.name != item.name:
                saved_data.name = item.name
            item.linked_name = item.name

            expressions_data = []
            for expr in saved_data.expressions:
                expressions_data.append({
                    "expression": expr.expression,
                    "frame": expr.frame
                })

            favorites.append({
                "name": item.name,
                "description": item.description,
                "expressions": expressions_data,
                "root_joint": saved_data.root_joint_name if saved_data.add_root_joint else ""
            })
        
        with open(favorites_path, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, indent=2)
        
        return len(favorites)
    except Exception as e:
        print(f"Error saving favorites: {str(e)}")
        return 0

def load_favorites_from_json(context):
    """Load saved favorite expression lists from a JSON file"""
    try:
        user_dir = bpy.utils.extension_path_user(__package__, create=True)
        favorites_path = os.path.join(user_dir, "favorites.json")
        
        if not os.path.exists(favorites_path):
            return 0
        
        with open(favorites_path, 'r', encoding='utf-8') as f:
            favorites = json.load(f)
        
        context.scene.facs_main.favorite_lists.clear()
        context.scene.facs_main.saved_expression_lists.clear()
        
        for fav in favorites:
            item = context.scene.facs_main.favorite_lists.add()
            item.name = fav["name"]
            item.linked_name = fav["name"]
            item.description = fav.get("description", "")
            
            saved_data = context.scene.facs_main.saved_expression_lists.add()
            saved_data.name = fav["name"]
            
            if "root_joint" in fav and fav["root_joint"]:
                saved_data.add_root_joint = True
                saved_data.root_joint_name = fav["root_joint"]
            
            for expr_data in fav.get("expressions", []):
                expr_item = saved_data.expressions.add()
                expr_item.expression = expr_data["expression"]
                expr_item.frame = expr_data["frame"]
        
        return len(favorites)
    except Exception as e:
        print(f"Error loading favorites: {str(e)}")
        return 0

def is_frame_in_use(context, frame_num, exclude_index=-1):
    for i, item in enumerate(context.scene.facs_main.expressions):
        if i != exclude_index and item.frame == frame_num:
            return True, item.expression
    return False, ""

def get_next_available_frame(context):
    """Find the lowest unused frame number by checking for gaps"""
    used_frames = [item.frame for item in context.scene.facs_main.expressions]
    if not used_frames:
        return 0
    
    used_frames.sort()
    
    expected = 0
    for frame in used_frames:
        if frame > expected:
            return expected
        expected = frame + 1
    
    return expected

def find_expression_index(context, expression_name):
    for i, item in enumerate(context.scene.facs_main.expressions):
        if item.expression == expression_name:
            return i
    return -1

def clean_frame_number(frame_text):
    if isinstance(frame_text, str):
        frame_text = frame_text.lstrip("0")
        if not frame_text:
            return 0
        try:
            return int(frame_text)
        except ValueError:
            return 0
    elif isinstance(frame_text, int):
        return frame_text
    else:
        return 0

def filter_text_update(self, context):
    global FILTERED_EXPRESSIONS_CACHE
    FILTERED_EXPRESSIONS_CACHE = {}
    
    force_ui_update()


def facs_order_mode_update(self, context):
    global FILTERED_EXPRESSIONS_CACHE
    FILTERED_EXPRESSIONS_CACHE = {}
    force_ui_update()

class FACS_UL_ExpressionList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.38, align=True)
        frame_row = split.row(align=True)
        frame_row.alignment = 'LEFT'
        frame_row.scale_x = 1.2
        frame_row.scale_y = 1.05
        frame_row.prop(item, "frame", text="")

        expr_row = split.row(align=True)
        expr_row.scale_y = 1.05
        expr_row.prop(item, "expression", text="", emboss=False)
    
    def draw_filter(self, context, layout):
        pass

class FACS_UL_FavoritesList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        desc_text = (item.description or "").strip() or "No description"
        if len(desc_text) > 30:
            desc_text = desc_text[:27] + "..."

        split = layout.split(factor=0.55, align=True)

        name_row = split.row(align=True)
        name_row.prop(item, "name", text="", emboss=False, icon='BOOKMARKS')

        desc_row = split.row(align=True)
        desc_row.alignment = 'RIGHT'
        desc_row.label(text=desc_text)

class FACS_OT_SaveExpressionList(Operator):
    bl_idname = "object.facs_save_expression_list"
    bl_label = "Save Expression List"
    bl_description = "Save the current expression list as a favorite"
    bl_options = {'REGISTER', 'UNDO'}
    
    list_name: StringProperty(
        name="Name",
        description="Name for this expression list",
        default="My Expression List"
    )
    
    description: StringProperty(
        name="Description",
        description="Optional description for this expression list",
        default=""
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def execute(self, context):
        main = context.scene.facs_main

        if not self.list_name:
            self.report({'ERROR'}, "Please provide a name for the expression list")
            return {'CANCELLED'}
        
        if len(main.expressions) == 0:
            self.report({'ERROR'}, "No expressions to save! Please add at least one expression.")
            return {'CANCELLED'}

        existing_favorite = find_favorite_by_name_or_link(main, self.list_name)
        if existing_favorite:
            old_key = existing_favorite.linked_name if existing_favorite.linked_name else existing_favorite.name
            existing_saved = get_saved_expression_list(main, old_key)
            if existing_saved:
                for i, saved in enumerate(main.saved_expression_lists):
                    if saved.as_pointer() == existing_saved.as_pointer():
                        main.saved_expression_lists.remove(i)
                        break

            existing_favorite.name = self.list_name
            existing_favorite.linked_name = self.list_name
            existing_favorite.description = self.description
            item = existing_favorite
        else:
            item = main.favorite_lists.add()
            item.name = self.list_name
            item.linked_name = self.list_name
            item.description = self.description
        
        saved_data = main.saved_expression_lists.add()
        saved_data.name = self.list_name
        
        saved_data.add_root_joint = main.props.add_root_joint
        saved_data.root_joint_name = main.props.root_joint_name
        
        for expr in main.expressions:
            new_expr = saved_data.expressions.add()
            new_expr.expression = expr.expression
            new_expr.frame = expr.frame
        
        save_favorites_to_json(context)
        
        self.report({'INFO'}, f"Saved expression list '{self.list_name}' with {len(main.expressions)} expressions")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_LoadExpressionList(Operator):
    bl_idname = "object.facs_load_expression_list"
    bl_label = "Load Expression List"
    bl_description = "Load a saved expression list"
    bl_options = {'REGISTER', 'UNDO'}
    
    list_name: StringProperty(default="")
    
    def execute(self, context):
        main = context.scene.facs_main

        if not self.list_name:
            self.report({'ERROR'}, "No expression list specified")
            return {'CANCELLED'}

        saved_data = get_saved_expression_list(main, self.list_name)
        if not saved_data:
            favorite = find_favorite_by_name_or_link(main, self.list_name)
            if favorite:
                lookup_name = favorite.linked_name if favorite.linked_name else favorite.name
                saved_data = get_saved_expression_list(main, lookup_name)
        
        if not saved_data:
            self.report({'ERROR'}, f"Expression list '{self.list_name}' not found")
            return {'CANCELLED'}
        
        main.expressions.clear()
        
        main.props.add_root_joint = saved_data.add_root_joint
        main.props.root_joint_name = saved_data.root_joint_name
        
        for expr in saved_data.expressions:
            new_expr = main.expressions.add()
            new_expr.expression = expr.expression
            new_expr.frame = expr.frame
            
            add_to_last_used(context, expr.expression)
        
        self.report({'INFO'}, f"Loaded expression list '{self.list_name}' with {len(saved_data.expressions)} expressions")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_DeleteExpressionList(Operator):
    bl_idname = "object.facs_delete_expression_list"
    bl_label = "Delete Expression List"
    bl_description = "Delete a saved expression list"
    bl_options = {'REGISTER', 'UNDO'}
    
    list_name: StringProperty(default="")
    
    def execute(self, context):
        main = context.scene.facs_main

        if not self.list_name:
            self.report({'ERROR'}, "No expression list specified")
            return {'CANCELLED'}

        favorite_index = -1
        favorite_key = self.list_name
        for i, item in enumerate(main.favorite_lists):
            if item.name == self.list_name or item.linked_name == self.list_name:
                favorite_index = i
                favorite_key = item.linked_name if item.linked_name else item.name
                break

        if favorite_index >= 0:
            main.favorite_lists.remove(favorite_index)

        for i, item in enumerate(main.saved_expression_lists):
            if item.name == favorite_key or item.name == self.list_name:
                main.saved_expression_lists.remove(i)
                break
        
        save_favorites_to_json(context)
        
        self.report({'INFO'}, f"Deleted expression list '{self.list_name}'")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_EditFavoriteDescription(Operator):
    bl_idname = "object.facs_edit_favorite_description"
    bl_label = "Edit Favorite Description"
    bl_description = "Edit description for a saved favorite list"
    bl_options = {'REGISTER', 'UNDO'}

    list_name: StringProperty(default="")
    description: StringProperty(
        name="Description",
        description="Description shown next to the favorite list name",
        default=""
    )

    def invoke(self, context, event):
        main = context.scene.facs_main

        favorite = None
        if self.list_name:
            favorite = find_favorite_by_name_or_link(main, self.list_name)

        if favorite is None and 0 <= main.active_favorite_index < len(main.favorite_lists):
            favorite = main.favorite_lists[main.active_favorite_index]

        if favorite is None:
            self.report({'ERROR'}, "No favorite list selected")
            return {'CANCELLED'}

        self.list_name = favorite.name
        self.description = favorite.description
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text=f"List: {self.list_name}", icon='BOOKMARKS')
        layout.prop(self, "description", text="Description")

    def execute(self, context):
        main = context.scene.facs_main
        favorite = find_favorite_by_name_or_link(main, self.list_name)

        if favorite is None:
            self.report({'ERROR'}, f"Favorite list '{self.list_name}' not found")
            return {'CANCELLED'}

        favorite.description = self.description.strip()
        save_favorites_to_json(context)

        self.report({'INFO'}, f"Updated description for '{favorite.name}'")
        force_ui_update()
        return {'FINISHED'}

class FACS_OT_LoadFavorites(Operator):
    bl_idname = "object.facs_load_favorites"
    bl_label = "Load Favorites"
    bl_description = "Load saved favorite expression lists"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        count = load_favorites_from_json(context)
        self.report({'INFO'}, f"Loaded {count} favorite expression lists")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_AddExpression(Operator):
    bl_idname = "object.facs_add_expression"
    bl_label = "Add Expression"
    bl_description = "Add a new FACS expression to the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    expression: StringProperty(
        name="Expression",
        description="Name of the FACS expression to add",
        default=""
    )
    
    frame: IntProperty(
        name="Frame",
        description="Frame number for this expression",
        default=0,
        min=0,
        subtype='NONE'
    )
    
    frame_text: StringProperty(
        name="Frame",
        description="Frame number (text input to handle leading zeros)",
        default=""
    )
    
    def invoke(self, context, event):
        self.frame = get_next_available_frame(context)
        self.frame_text = str(self.frame)
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        
        layout.prop(self, "expression")
        layout.prop(self, "frame_text", text="Frame")
        
        try:
            frame_num = int(self.frame_text)
            in_use, expr = is_frame_in_use(context, frame_num)
            if in_use:
                layout.label(text=f"Warning: Frame {frame_num} already used by '{expr}'", icon='ERROR')
        except ValueError:
            layout.label(text="Please enter a valid number for Frame", icon='ERROR')
    
    def execute(self, context):
        if not self.expression:
            self.report({'ERROR'}, "Expression name cannot be empty")
            return {'CANCELLED'}
        
        try:
            frame_num = clean_frame_number(self.frame_text)
        except ValueError:
            self.report({'ERROR'}, f"Invalid frame number: {self.frame_text}")
            return {'CANCELLED'}
            
        expr_idx = find_expression_index(context, self.expression)
        if expr_idx >= 0:
            old_frame = context.scene.facs_main.expressions[expr_idx].frame
            context.scene.facs_main.expressions.remove(expr_idx)
            self.report({'INFO'}, f"Replaced '{self.expression}' from frame {old_frame}")
        
        item = context.scene.facs_main.expressions.add()
        item.expression = self.expression
        item.frame = frame_num
        context.scene.facs_main.active_expression_index = len(context.scene.facs_main.expressions) - 1
        
        add_to_last_used(context, self.expression)
        
        expressions = context.scene.facs_main.expressions
        sorted_indices = sorted(range(len(expressions)), key=lambda i: expressions[i].frame)
        for i, target_idx in enumerate(sorted_indices):
            if i != target_idx:
                expressions.move(target_idx, i)
        
        for i, expr in enumerate(context.scene.facs_main.expressions):
            if expr.expression == self.expression and expr.frame == frame_num:
                context.scene.facs_main.active_expression_index = i
                break
        
        self.report({'INFO'}, f"Added '{self.expression}' at Frame {frame_num}")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_AutoNumber(Operator):
    bl_idname = "object.facs_auto_number"
    bl_label = "Auto Number"
    bl_description = "Automatically assign sequential frame numbers (0, 1, 2...)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        expressions = context.scene.facs_main.expressions
        for i, item in enumerate(expressions):
            item.frame = i
        
        self.report({'INFO'}, f"Auto-numbered {len(expressions)} expressions sequentially")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_ReverseNumber(Operator):
    bl_idname = "object.facs_reverse_number"
    bl_label = "Reverse Numbers"
    bl_description = "Reverse list order (expression names and frame numbers together)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        expressions = context.scene.facs_main.expressions
        
        if len(expressions) < 2:
            self.report({'INFO'}, "Nothing to reverse: less than 2 expressions")
            return {'FINISHED'}

        previous_index = context.scene.facs_main.active_expression_index
        reversed_items = [(item.expression, item.frame) for item in reversed(expressions)]

        for item, (expr_name, frame_num) in zip(expressions, reversed_items):
            item.expression = expr_name
            item.frame = frame_num

        if 0 <= previous_index < len(expressions):
            context.scene.facs_main.active_expression_index = len(expressions) - 1 - previous_index

        self.report({'INFO'}, f"Reversed {len(expressions)} expression rows")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_RemoveExpression(Operator):
    bl_idname = "object.facs_remove_expression"
    bl_label = "Remove Expression"
    bl_description = "Remove the selected FACS expression from the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if len(context.scene.facs_main.expressions) > 0:
            idx = context.scene.facs_main.active_expression_index
            item = context.scene.facs_main.expressions[idx]
            
            expr_name = item.expression
            frame_num = item.frame
            
            context.scene.facs_main.expressions.remove(idx)
            context.scene.facs_main.active_expression_index = min(idx, len(context.scene.facs_main.expressions) - 1)
            
            self.report({'INFO'}, f"Removed '{expr_name}' from Frame {frame_num}")
            
            force_ui_update()
            
        return {'FINISHED'}

class FACS_OT_MoveExpression(Operator):
    bl_idname = "object.facs_move_expression"
    bl_label = "Move Expression"
    bl_description = "Move the selected FACS expression in the list and update frame numbers accordingly"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: StringProperty(default="UP")
    
    def execute(self, context):
        expressions = context.scene.facs_main.expressions
        idx = context.scene.facs_main.active_expression_index
        
        if len(expressions) < 2:
            return {'CANCELLED'}
            
        if self.direction == "UP" and idx > 0:
            curr_frame = expressions[idx].frame
            prev_frame = expressions[idx-1].frame
            
            expressions.move(idx, idx - 1)
            
            expressions[idx].frame = curr_frame
            expressions[idx-1].frame = prev_frame
            
            context.scene.facs_main.active_expression_index = idx - 1
            
            self.report({'INFO'}, f"Moved '{expressions[idx-1].expression}' up and swapped frame numbers")
            
        elif self.direction == "DOWN" and idx < len(expressions) - 1:
            curr_frame = expressions[idx].frame
            next_frame = expressions[idx+1].frame
            
            expressions.move(idx, idx + 1)
            
            expressions[idx].frame = curr_frame
            expressions[idx+1].frame = next_frame
            
            context.scene.facs_main.active_expression_index = idx + 1
            
            self.report({'INFO'}, f"Moved '{expressions[idx+1].expression}' down and swapped frame numbers")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_AddPreset(Operator):
    bl_idname = "object.facs_add_preset"
    bl_label = "Add Preset Expression"
    bl_description = "Add a preset FACS expression to the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset: StringProperty(default="")
    
    preserve_state: BoolProperty(default=True)
    
    def execute(self, context):
        if not self.preset:
            return {'CANCELLED'}
            
        expr_idx = find_expression_index(context, self.preset)
        if expr_idx >= 0:
            old_frame = context.scene.facs_main.expressions[expr_idx].frame
            context.scene.facs_main.expressions.remove(expr_idx)
            self.report({'INFO'}, f"Replaced '{self.preset}' from frame {old_frame}")
        
        active_categories = get_active_preset_categories(context)
        expanded_categories = {}
        if self.preserve_state:
            for category in active_categories.keys():
                attr_name = f"show_{category.lower()}"
                if hasattr(context.scene.facs_main, attr_name):
                    expanded_categories[attr_name] = getattr(context.scene.facs_main, attr_name)
        
        if len(context.scene.facs_main.expressions) > 0:
            new_frame = max(item.frame for item in context.scene.facs_main.expressions) + 1
        else:
            new_frame = 0
        
        item = context.scene.facs_main.expressions.add()
        item.expression = self.preset
        item.frame = new_frame
        context.scene.facs_main.active_expression_index = len(context.scene.facs_main.expressions) - 1
        
        add_to_last_used(context, self.preset)
        
        expressions = context.scene.facs_main.expressions
        sorted_indices = sorted(range(len(expressions)), key=lambda i: expressions[i].frame)
        for i, target_idx in enumerate(sorted_indices):
            if i != target_idx:
                expressions.move(target_idx, i)
        
        if self.preserve_state:
            for attr_name, state in expanded_categories.items():
                setattr(context.scene.facs_main, attr_name, state)
        
        self.report({'INFO'}, f"Added '{self.preset}' at Frame {new_frame}")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_AddPresetCategory(Operator):
    bl_idname = "object.facs_add_preset_category"
    bl_label = "Add All in Category"
    bl_description = "Add all preset FACS expressions in this category"
    bl_options = {'REGISTER', 'UNDO'}
    
    category: StringProperty(default="")
    
    def execute(self, context):
        active_categories = get_active_preset_categories(context)
        if not self.category or self.category not in active_categories:
            return {'CANCELLED'}
        
        expanded_categories = {}
        for category in active_categories.keys():
            attr_name = f"show_{category.lower()}"
            if hasattr(context.scene.facs_main, attr_name):
                expanded_categories[attr_name] = getattr(context.scene.facs_main, attr_name)
        
        expressions_to_remove = []
        for i, item in enumerate(context.scene.facs_main.expressions):
            if item.expression in active_categories[self.category]:
                expressions_to_remove.append(i)
        
        removed_count = 0
        for i in sorted(expressions_to_remove, reverse=True):
            context.scene.facs_main.expressions.remove(i)
            removed_count += 1
        
        added_count = 0
        
        start_frame = get_next_available_frame(context)
        
        for i, expr in enumerate(active_categories[self.category]):
            current_frame = start_frame + i
            while is_frame_in_use(context, current_frame)[0]:
                current_frame += 1
                
            item = context.scene.facs_main.expressions.add()
            item.expression = expr
            item.frame = current_frame
            
            add_to_last_used(context, expr)
            
            added_count += 1
        
        expressions = context.scene.facs_main.expressions
        sorted_indices = sorted(range(len(expressions)), key=lambda i: expressions[i].frame)
        for i, target_idx in enumerate(sorted_indices):
            if i != target_idx:
                expressions.move(target_idx, i)
        
        context.scene.facs_main.active_expression_index = len(context.scene.facs_main.expressions) - 1
        
        for attr_name, state in expanded_categories.items():
            setattr(context.scene.facs_main, attr_name, state)
        
        self.report({'INFO'}, f"Added {added_count} expressions from {self.category} category. Replaced {removed_count} duplicates.")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_AddRequired(Operator):
    bl_idname = "object.facs_add_required"
    bl_label = "Add Required Expressions"
    bl_description = "Add all required FACS expressions in sequence"
    bl_options = {'REGISTER', 'UNDO'}

    required_order: EnumProperty(
        name="Required Order",
        description="Choose which required expression order to apply",
        items=FACS_ORDER_ITEMS,
        default='NEW'
    )
    
    def invoke(self, context, event):
        props = context.scene.facs_main.props
        self.required_order = get_active_order_mode(context)
        if getattr(props, "show_add_required_order_picker", True):
            return context.window_manager.invoke_props_dialog(self, width=380)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "required_order", text="Order")
        draw_order_warning(layout)
        if len(context.scene.facs_main.expressions) > 0:
            layout.label(text="Current expression list will be replaced.", icon='ERROR')
    
    def execute(self, context):
        props = context.scene.facs_main.props
        active_categories = get_active_preset_categories(context, override_mode=self.required_order)
        required_expressions = active_categories.get("Required", [])
        if not required_expressions:
            self.report({'ERROR'}, "No required expression profile found for the selected order")
            return {'CANCELLED'}

        if hasattr(props, "facs_order_mode"):
            props.facs_order_mode = self.required_order
        if hasattr(props, "show_add_required_order_picker"):
            props.show_add_required_order_picker = False

        expanded_categories = {}
        for category in FACS_ALL_CATEGORY_NAMES:
            attr_name = f"show_{category.lower()}"
            if hasattr(context.scene.facs_main, attr_name):
                expanded_categories[attr_name] = getattr(context.scene.facs_main, attr_name)
        
        if len(context.scene.facs_main.expressions) > 0:
            bpy.ops.object.facs_clear_all(confirm=False)
        
        for i, expr in enumerate(required_expressions):
            item = context.scene.facs_main.expressions.add()
            item.expression = expr
            item.frame = i
            
            add_to_last_used(context, expr)
        
        for attr_name, state in expanded_categories.items():
            setattr(context.scene.facs_main, attr_name, state)
        
        self.report({'INFO'}, f"Added {len(required_expressions)} required expressions ({get_facs_order_label(self.required_order)})")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_ClearAll(Operator):
    bl_idname = "object.facs_clear_all"
    bl_label = "Clear All Expressions"
    bl_description = "Remove all expressions from the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    confirm: BoolProperty(default=True)
    
    def invoke(self, context, event):
        if self.confirm:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)
    
    def execute(self, context):
        count = len(context.scene.facs_main.expressions)
        context.scene.facs_main.expressions.clear()
        context.scene.facs_main.active_expression_index = 0
        self.report({'INFO'}, f"Cleared {count} expressions")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_RemoveAllCustomProps(Operator):
    bl_idname = "object.facs_remove_all_custom_props"
    bl_label = "Remove Custom Properties"
    bl_description = "Remove all custom properties from the target object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.facs_main.props
        target_obj = get_target_object_in_active_scene(context, props.target_object)
        
        if not target_obj:
            self.report({'ERROR'}, f"Target object '{props.target_object}' not found in active scene!")
            return {'CANCELLED'}
        
        prop_keys = list(target_obj.keys())
        count = len(prop_keys)
        
        removed_count = 0
        for prop_key in prop_keys:
            try:
                del target_obj[prop_key]
                removed_count += 1
            except Exception as e:
                self.report({'WARNING'}, f"Could not remove property '{prop_key}': {str(e)}")
        
        self.report({'INFO'}, f"Removed {removed_count} of {count} custom properties from {target_obj.name}")
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_ClearFilter(Operator):
    bl_idname = "object.facs_clear_filter"
    bl_label = "Clear Filter"
    bl_description = "Clear the expression search filter"
    
    def execute(self, context):
        context.scene.facs_main.props.filter_expressions = ""
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_ExportToText(Operator):
    bl_idname = "object.facs_export_to_txt"
    bl_label = "Export to Text File"
    bl_description = "Export expressions to a text file on disk"
    
    filepath: StringProperty(
        name="File Path",
        description="Path to save the text file",
        default="//FACS_Expressions.txt",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if not self.filepath.lower().endswith('.txt'):
            self.filepath += '.txt'
            
        content = "# FACS Expressions\n"
        content += "# Format: Frame Number, Expression Name\n\n"
        
        for item in context.scene.facs_main.expressions:
            content += f"Frame{item.frame}, {item.expression}\n"
            
        if context.scene.facs_main.props.add_root_joint:
            content += f"\nRootFaceJoint, {context.scene.facs_main.props.root_joint_name}\n"
        
        try:
            with open(bpy.path.abspath(self.filepath), 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.report({'INFO'}, f"Exported {len(context.scene.facs_main.expressions)} expressions to {os.path.basename(self.filepath)}")
            
            force_ui_update()
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting file: {str(e)}")
            return {'CANCELLED'}

class FACS_OT_ImportFromText(Operator):
    bl_idname = "object.facs_import_from_txt"
    bl_label = "Import from Text File"
    bl_description = "Import expressions from a text file on disk"
    
    filepath: StringProperty(
        name="File Path",
        description="Path to the text file to import",
        default="//FACS_Expressions.txt",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        file_path = bpy.path.abspath(self.filepath)
        if not os.path.exists(file_path):
            self.report({'ERROR'}, f"File not found: {file_path}")
            return {'CANCELLED'}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            added_count = 0
            replaced_count = 0
            
            expanded_categories = {}
            for category in FACS_ALL_CATEGORY_NAMES:
                attr_name = f"show_{category.lower()}"
                if hasattr(context.scene.facs_main, attr_name):
                    expanded_categories[attr_name] = getattr(context.scene.facs_main, attr_name)
            
            if len(context.scene.facs_main.expressions) > 0:
                bpy.ops.object.facs_clear_all()
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                match = re.match(r'Frame(\d+),\s*(.+)', line)
                if match:
                    frame_num = clean_frame_number(match.group(1))
                    expr_name = match.group(2).strip()
                    
                    in_use, _ = is_frame_in_use(context, frame_num)
                    if in_use:
                        replaced_count += 1
                        for i, item in enumerate(context.scene.facs_main.expressions):
                            if item.frame == frame_num:
                                context.scene.facs_main.expressions.remove(i)
                                break
                    
                    item = context.scene.facs_main.expressions.add()
                    item.frame = frame_num
                    item.expression = expr_name
                    
                    add_to_last_used(context, expr_name)
                    
                    added_count += 1
                    
                match = re.match(r'RootFaceJoint,\s*(.+)', line)
                if match:
                    joint_name = match.group(1).strip()
                    context.scene.facs_main.props.add_root_joint = True
                    context.scene.facs_main.props.root_joint_name = joint_name
            
            expressions = context.scene.facs_main.expressions
            sorted_indices = sorted(range(len(expressions)), key=lambda i: expressions[i].frame)
            for i, target_idx in enumerate(sorted_indices):
                if i != target_idx:
                    expressions.move(target_idx, i)
            
            for attr_name, state in expanded_categories.items():
                setattr(context.scene.facs_main, attr_name, state)
            
            self.report({'INFO'}, f"Imported {added_count} expressions from {os.path.basename(self.filepath)}. Replaced {replaced_count} duplicates.")
            
            force_ui_update()
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error importing file: {str(e)}")
            return {'CANCELLED'}

class FACS_OT_CancelApply(Operator):
    bl_idname = "object.facs_cancel_apply"
    bl_label = "Cancel Apply"
    bl_description = "Cancel applying FACS properties"
    
    def execute(self, context):
        context.scene.facs_main.props.cancel_apply = True
        
        force_ui_update()
        
        return {'FINISHED'}

class FACS_OT_ApplyProperties(Operator):
    bl_idname = "object.facs_apply_properties"
    bl_label = "Apply FACS Properties"
    bl_description = "Apply all FACS expressions as custom properties to the target object"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    target_obj = None
    progress = 0
    total_props = 0
    expressions_to_add = []
    is_running = False
    
    def invoke(self, context, event):
        props = context.scene.facs_main.props
        
        self.target_obj = get_target_object_in_active_scene(context, props.target_object)
        if not self.target_obj:
            self.report({'ERROR'}, f"Target object '{props.target_object}' not found in active scene!")
            return {'CANCELLED'}
        
        if len(context.scene.facs_main.expressions) == 0:
            self.report({'ERROR'}, "No expressions to add! Please add at least one expression.")
            return {'CANCELLED'}
        
        self.progress = 0
        self.total_props = len(context.scene.facs_main.expressions)
        if props.add_root_joint:
            self.total_props += 1
        
        props.is_applying = True
        props.apply_progress = 0.0
        
        self.expressions_to_add = []
        
        if props.add_root_joint:
            self.expressions_to_add.append(("RootFaceJoint", props.root_joint_name))
        
        for item in context.scene.facs_main.expressions:
            prop_name = f"Frame{item.frame}"
            self.expressions_to_add.append((prop_name, item.expression))
        
        for key in list(self.target_obj.keys()):
            del self.target_obj[key]
        
        self._timer = context.window_manager.event_timer_add(props.delay, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.is_running = True
        
        force_ui_update()
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        props = context.scene.facs_main.props
        
        if props.cancel_apply:
            self.cancel(context)
            props.cancel_apply = False
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}
        
        if event.type == 'TIMER' and self.is_running:
            if self.progress >= self.total_props:
                self.cancel(context)
                self.report({'INFO'}, f"Added {self.total_props} properties to {self.target_obj.name}")
                return {'FINISHED'}
            
            prop_name, prop_value = self.expressions_to_add[self.progress]
            self.target_obj[prop_name] = prop_value
            
            self.progress += 1
            props.apply_progress = self.progress / self.total_props
            
            force_ui_update()
        
        return {'PASS_THROUGH'}
    
    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self.is_running = False
        self._timer = None
        context.scene.facs_main.props.is_applying = False
        context.scene.facs_main.props.apply_progress = 0.0
        
        force_ui_update()

    def execute(self, context):
        return self.invoke(context, None)

class FACS_OT_OpenDiscordServer(Operator):
    bl_idname = "object.facs_open_discord"
    bl_label = "Contact Support"
    bl_description = "Open contact links"
    
    def execute(self, context):
        import webbrowser
        webbrowser.open("https://links.cloud3dworks.art/")
        return {'FINISHED'}

class FACS_OT_SetTabWorkflow(Operator):
    bl_idname = "object.facs_set_tab_workflow"
    bl_label = "Workflow"
    bl_description = ""
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.facs_main.props.ui_tab = 'WORKFLOW'
        force_ui_update()
        return {'FINISHED'}

class FACS_OT_SetTabFavorites(Operator):
    bl_idname = "object.facs_set_tab_favorites"
    bl_label = "Favorites"
    bl_description = ""
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.facs_main.props.ui_tab = 'FAVORITES'
        force_ui_update()
        return {'FINISHED'}

class FACS_OT_SetTabBrowse(Operator):
    bl_idname = "object.facs_set_tab_browse"
    bl_label = "Browse"
    bl_description = ""
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.facs_main.props.ui_tab = 'BROWSE'
        force_ui_update()
        return {'FINISHED'}


class FACS_OT_OpenSettings(Operator):
    bl_idname = "object.facs_open_settings"
    bl_label = "FACS Settings"
    bl_description = "Switch between old and new FACS order profiles"
    bl_options = {'REGISTER', 'UNDO'}

    facs_order_mode: EnumProperty(
        name="FACS Order",
        description="Default order profile used by Add Required, Browse, and Search",
        items=FACS_ORDER_ITEMS,
        default='NEW'
    )

    def invoke(self, context, event):
        self.facs_order_mode = get_active_order_mode(context)
        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "facs_order_mode", text="Profile")
        draw_order_warning(layout)

    def execute(self, context):
        props = context.scene.facs_main.props
        if hasattr(props, "facs_order_mode"):
            props.facs_order_mode = self.facs_order_mode
        self.report({'INFO'}, f"FACS order set to {get_facs_order_label(self.facs_order_mode)}")
        force_ui_update()
        return {'FINISHED'}

class FACS_SavedExpressionList(PropertyGroup):
    """Stores a saved expression list"""
    name: StringProperty(
        name="Name",
        description="Name of this saved expression list",
        default="Unnamed"
    )
    
    expressions: CollectionProperty(type=FACS_ExpressionItem)
    
    add_root_joint: BoolProperty(
        name="Add RootFaceJoint",
        description="Automatically add the RootFaceJoint property",
        default=True
    )
    
    root_joint_name: StringProperty(
        name="Root Joint Name",
        description="Value for the RootFaceJoint property",
        default="DynamicHead"
    )

class FACSProperties(PropertyGroup):
    target_object: StringProperty(
        name="Target Object",
        description="Name of the object to add properties to",
        default="Head_Geo"
    )
    
    delay: FloatProperty(
        name="Delay",
        description="Delay between adding each property (seconds)",
        default=0.03,
        min=0.01,
        max=1.0,
        subtype='NONE'
    )
    
    add_root_joint: BoolProperty(
        name="Add RootFaceJoint",
        description="Automatically add the RootFaceJoint property",
        default=True
    )
    
    root_joint_name: StringProperty(
        name="Root Joint Name",
        description="Value for the RootFaceJoint property",
        default="DynamicHead"
    )

    facs_order_mode: EnumProperty(
        name="FACS Order",
        description="Default expression order profile used throughout the UI",
        items=FACS_ORDER_ITEMS,
        default='NEW',
        update=facs_order_mode_update
    )

    show_add_required_order_picker: BoolProperty(
        name="Show Add Required Order Picker",
        description="Show the new and old order choice the first time Add Required is used",
        default=True
    )
    
    filter_expressions: StringProperty(
        name="Filter",
        description="Filter expressions by name",
        default="",
        options={'TEXTEDIT_UPDATE'},
        update=filter_text_update
    )
    
    is_applying: BoolProperty(
        name="Is Applying",
        description="Whether properties are currently being applied",
        default=False
    )
    
    apply_progress: FloatProperty(
        name="Apply Progress",
        description="Progress of applying properties",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE'
    )
    
    cancel_apply: BoolProperty(
        name="Cancel Apply",
        description="Flag to cancel the apply operation",
        default=False
    )
    
    show_target_settings: BoolProperty(
        name="Show Target Settings",
        description="Show or hide target settings section",
        default=True
    )
    
    show_favorites: BoolProperty(
        name="Show Favorites",
        description="Show or hide favorites section",
        default=True
    )
    
    show_expression_list: BoolProperty(
        name="Show Expression List",
        description="Show or hide expression list section",
        default=True
    )
    
    show_search: BoolProperty(
        name="Show Search",
        description="Show or hide search section",
        default=True
    )
    
    show_categories: BoolProperty(
        name="Show Categories",
        description="Show or hide categories section",
        default=False
    )

    ui_tab: EnumProperty(
        name="View",
        description="Switch between FACS views",
        items=[
            ('WORKFLOW', "Workflow", "Build and apply the expression list"),
            ('FAVORITES', "Favorites", "Save, load, and manage favorite lists"),
            ('BROWSE', "Browse", "Search and add preset expressions")
        ],
        default='WORKFLOW'
    )

class FACS_MainProperties(PropertyGroup):
    expressions: CollectionProperty(type=FACS_ExpressionItem)
    active_expression_index: IntProperty(default=0)
    
    last_used_expressions: CollectionProperty(type=PropertyGroup)
    
    favorite_lists: CollectionProperty(type=FACS_FavoriteListItem)
    active_favorite_index: IntProperty(default=0)
    
    saved_expression_lists: CollectionProperty(type=FACS_SavedExpressionList)
    
    expression_suggestions: CollectionProperty(type=PropertyGroup)
    
    props: PointerProperty(type=FACSProperties)

class FACS_PT_Panel(Panel):
    bl_label = "FACS Expression Manager"
    bl_idname = "PT_FACSExpressionPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FACS'

    def _draw_side_tabs(self, layout, props):
        col = layout.column(align=True)
        col.scale_x = 1.08

        row = col.row(align=True)
        row.scale_y = 1.20
        row.operator("object.facs_open_discord", text="", icon='URL')

        col.separator(factor=1.15)

        row = col.row(align=True)
        row.scale_y = 1.35
        row.operator(
            "object.facs_set_tab_workflow",
            text="",
            icon='PRESET',
            depress=(props.ui_tab == 'WORKFLOW')
        )

        row = col.row(align=True)
        row.scale_y = 1.35
        row.operator(
            "object.facs_set_tab_favorites",
            text="",
            icon='FILE_TICK',
            depress=(props.ui_tab == 'FAVORITES')
        )

        row = col.row(align=True)
        row.scale_y = 1.35
        row.operator(
            "object.facs_set_tab_browse",
            text="",
            icon='VIEWZOOM',
            depress=(props.ui_tab == 'BROWSE')
        )

        col.separator(factor=1.0)
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("object.facs_open_settings", text="", icon='PREFERENCES')

    def _draw_target_settings_content(self, context, layout, props):
        target_name = (props.target_object or "").strip()
        target_obj = get_target_object_in_active_scene(context, target_name) if target_name else None
        global_obj = bpy.data.objects.get(target_name) if target_name else None

        target_col = layout.column(align=False)
        target_col.use_property_split = True
        target_col.use_property_decorate = False
        target_col.label(text="Target Object", icon='OBJECT_DATA')

        input_col = target_col.column(align=True)
        input_col.prop(props, "target_object", text="Name")

        status_row = target_col.row(align=True)
        status_row.scale_y = 1.02
        if target_obj is None:
            status_row.alert = True
            if target_name:
                if global_obj is not None:
                    status_row.label(text=f"Not in active scene: {target_name}", icon='ERROR')
                else:
                    status_row.label(text=f"Not found: {target_name}", icon='ERROR')
            else:
                status_row.label(text="No target object set", icon='ERROR')
        else:
            status_row.label(text=f"Found: {target_obj.name}", icon='CHECKMARK')

        layout.separator(factor=0.55)

        options_col = layout.column(align=False)
        options_col.use_property_split = True
        options_col.use_property_decorate = False
        options_col.label(text="Apply Options", icon='SETTINGS')
        options_col.prop(props, "delay", text="Delay (sec)")

        options_col.separator(factor=0.25)
        options_col.prop(props, "add_root_joint", text="Add RootFaceJoint")
        if props.add_root_joint:
            root_col = options_col.column(align=False)
            root_col.prop(props, "root_joint_name", text="RootFaceJoint")

    def _draw_favorites_content(self, layout, main):
        action_col = layout.column(align=True)
        action_col.operator("object.facs_save_expression_list", text="Save Current List", icon='PLUS')
        action_col.operator("object.facs_load_favorites", text="Reload Saved Lists", icon='FILE_REFRESH')

        hint_row = layout.row()
        hint_row.scale_y = 0.9
        hint_row.label(text=f"Saved lists: {len(main.favorite_lists)}", icon='BOOKMARKS')

        if len(main.favorite_lists) > 0:
            row = layout.row()
            row.template_list(
                "FACS_UL_FavoritesList", "favorite_lists",
                main, "favorite_lists",
                main, "active_favorite_index",
                rows=5
            )
            valid_index = 0 <= main.active_favorite_index < len(main.favorite_lists)
            if valid_index:
                selected = main.favorite_lists[main.active_favorite_index]

                lookup_name = selected.linked_name if selected.linked_name else selected.name
                saved_data = (
                    get_saved_expression_list(main, selected.name) or
                    get_saved_expression_list(main, lookup_name)
                )

                info_box = layout.box()
                info_box.label(text=f"Selected: {selected.name}", icon='CHECKMARK')
                if selected.description:
                    info_box.label(text=selected.description, icon='INFO')
                info_box.label(
                    text=f"Expressions: {len(saved_data.expressions) if saved_data else 0}",
                    icon='PRESET'
                )

                button_row = layout.row(align=True)
                load_op = button_row.operator("object.facs_load_expression_list", text="Load", icon='IMPORT')
                load_op.list_name = selected.name
                edit_op = button_row.operator("object.facs_edit_favorite_description", text="Edit Desc", icon='GREASEPENCIL')
                edit_op.list_name = selected.name
                del_op = button_row.operator("object.facs_delete_expression_list", text="Delete", icon='TRASH')
                del_op.list_name = selected.name
        else:
            layout.label(text="No saved expression lists yet.", icon='INFO')

    def _draw_expression_list_content(self, context, layout, main, props):
        list_row = layout.row()
        list_row.template_list(
            "FACS_UL_ExpressionList", "facs_expressions",
            main, "expressions",
            main, "active_expression_index",
            rows=10
        )

        side_col = list_row.column(align=True)
        side_col.operator("object.facs_add_expression", text="", icon='ADD')
        side_col.operator("object.facs_remove_expression", text="", icon='REMOVE')
        side_col.separator()
        side_col.operator("object.facs_move_expression", text="", icon='TRIA_UP').direction = "UP"
        side_col.operator("object.facs_move_expression", text="", icon='TRIA_DOWN').direction = "DOWN"

        row = layout.row(align=True)
        row.operator("object.facs_add_required", text="Add Required", icon='CHECKBOX_HLT')
        row.operator("object.facs_clear_all", text="Clear All", icon='X')

        layout.separator(factor=0.3)

        row = layout.row(align=True)
        row.operator("object.facs_auto_number", text="Auto Number", icon='LINENUMBERS_ON')
        row.operator("object.facs_reverse_number", text="Reverse", icon='ARROW_LEFTRIGHT')

        layout.separator(factor=0.3)

        row = layout.row(align=True)
        row.operator("object.facs_export_to_txt", text="Export", icon='EXPORT')
        row.operator("object.facs_import_from_txt", text="Import", icon='IMPORT')

    def _draw_search_content(self, context, layout, main, props, limit=12):
        search_row = layout.row(align=True)
        search_row.prop(props, "filter_expressions", text="", icon='VIEWZOOM')
        if props.filter_expressions:
            search_row.operator("object.facs_clear_filter", text="", icon='X')

        if props.filter_expressions:
            filtered_exprs = improved_search_filter(
                props.filter_expressions.lower().strip(),
                get_active_all_expressions(context)
            )
            if filtered_exprs:
                grid = layout.grid_flow(row_major=True, columns=2, even_columns=True)
                for expr in filtered_exprs[:limit]:
                    op = grid.row(align=True).operator("object.facs_add_preset", text=expr)
                    op.preset = expr
            else:
                layout.label(text="No matching expressions found", icon='INFO')
        elif len(main.last_used_expressions) > 0:
            layout.label(text="Recently used", icon='RECOVER_LAST')
            grid = layout.grid_flow(row_major=True, columns=2, even_columns=True)
            for item in main.last_used_expressions:
                op = grid.row(align=True).operator("object.facs_add_preset", text=item.name)
                op.preset = item.name

    def _draw_categories_content(self, context, layout, main):
        active_categories = get_active_preset_categories(context)
        for category, expressions in active_categories.items():
            attr_name = f"show_{category.lower()}"
            cat_box = layout.box()
            cat_header = cat_box.row(align=True)
            cat_header.prop(
                main,
                attr_name,
                text="",
                icon='TRIA_DOWN' if getattr(main, attr_name) else 'TRIA_RIGHT',
                emboss=False
            )
            cat_header.label(text=f"{category} ({len(expressions)})", icon='PRESET')
            add_all = cat_header.operator("object.facs_add_preset_category", text="", icon='ADD')
            add_all.category = category

            if getattr(main, attr_name):
                grid = cat_box.grid_flow(row_major=True, columns=2, even_columns=True)
                for expr in expressions:
                    op = grid.row(align=True).operator("object.facs_add_preset", text=expr)
                    op.preset = expr

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        main = context.scene.facs_main
        props = main.props

        main_row = layout.row(align=False)
        nav_col = main_row.column(align=True)
        content_col = main_row.column(align=False)

        self._draw_side_tabs(nav_col, props)
        content_col.separator(factor=0.25)

        if props.ui_tab == 'WORKFLOW':
            target_box = content_col.box()
            target_header = target_box.row(align=True)
            target_header.prop(
                props,
                "show_target_settings",
                text="",
                icon='TRIA_DOWN' if props.show_target_settings else 'TRIA_RIGHT',
                emboss=False
            )
            target_header.label(text="Target Settings", icon='OBJECT_DATA')
            if props.show_target_settings:
                self._draw_target_settings_content(context, target_box, props)

            content_col.separator(factor=0.22)
            expr_box = content_col.box()
            expr_header = expr_box.row(align=True)
            expr_header.prop(
                props,
                "show_expression_list",
                text="",
                icon='TRIA_DOWN' if props.show_expression_list else 'TRIA_RIGHT',
                emboss=False
            )
            expr_count = len(main.expressions)
            expr_header.label(text=f"Expressions ({expr_count})", icon='PRESET')
            if props.show_expression_list:
                self._draw_expression_list_content(context, expr_box, main, props)

            content_col.separator(factor=0.35)

            if props.is_applying:
                progress_row = content_col.row(align=True)
                progress_row.prop(props, "apply_progress", text="Applying")
                progress_row.operator("object.facs_cancel_apply", text="", icon='X')

            apply_row = content_col.row(align=True)
            apply_row.scale_y = 1.4
            apply_row.operator("object.facs_apply_properties", text="Apply FACS Properties", icon='CHECKMARK')

            content_col.operator("object.facs_remove_all_custom_props", text="Remove Custom Props", icon='TRASH')

        elif props.ui_tab == 'FAVORITES':
            favorites_box = content_col.box()
            favorites_header = favorites_box.row(align=True)
            favorites_header.prop(
                props,
                "show_favorites",
                text="",
                icon='TRIA_DOWN' if props.show_favorites else 'TRIA_RIGHT',
                emboss=False
            )
            favorites_header.label(text="Favorite Lists", icon='FILE_TICK')
            if props.show_favorites:
                self._draw_favorites_content(favorites_box, main)

        elif props.ui_tab == 'BROWSE':
            search_box = content_col.box()
            search_header = search_box.row(align=True)
            search_header.prop(
                props,
                "show_search",
                text="",
                icon='TRIA_DOWN' if props.show_search else 'TRIA_RIGHT',
                emboss=False
            )
            search_header.label(text="Search Expressions", icon='VIEWZOOM')
            if props.show_search:
                self._draw_search_content(context, search_box, main, props, limit=14)

            content_col.separator(factor=0.22)
            categories_box = content_col.box()
            categories_header = categories_box.row(align=True)
            categories_header.prop(
                props,
                "show_categories",
                text="",
                icon='TRIA_DOWN' if props.show_categories else 'TRIA_RIGHT',
                emboss=False
            )
            categories_header.label(text="Expression Categories", icon='PRESET')
            if props.show_categories:
                self._draw_categories_content(context, categories_box, main)


@persistent
def load_favorites_handler(dummy):
    """Load favorites when Blender starts or a new file is loaded"""
    try:
        if bpy.context.scene:
            load_favorites_from_json(bpy.context)
    except Exception as e:
        print(f"Error loading favorites on startup: {str(e)}")

classes = [
    FACS_ExpressionItem,
    FACS_FavoriteListItem,
    FACS_SavedExpressionList,
    FACS_UL_ExpressionList,
    FACS_UL_FavoritesList,
    FACS_OT_AddExpression,
    FACS_OT_RemoveExpression,
    FACS_OT_MoveExpression,
    FACS_OT_AddPreset,
    FACS_OT_AddPresetCategory,
    FACS_OT_AddRequired,
    FACS_OT_ClearAll,
    FACS_OT_RemoveAllCustomProps,
    FACS_OT_ClearFilter,
    FACS_OT_ExportToText,
    FACS_OT_ImportFromText,
    FACS_OT_ApplyProperties,
    FACS_OT_AutoNumber,
    FACS_OT_ReverseNumber,
    FACS_OT_CancelApply,
    FACS_OT_OpenDiscordServer,
    FACS_OT_SetTabWorkflow,
    FACS_OT_SetTabFavorites,
    FACS_OT_SetTabBrowse,
    FACS_OT_OpenSettings,
    FACS_OT_SaveExpressionList,
    FACS_OT_LoadExpressionList,
    FACS_OT_DeleteExpressionList,
    FACS_OT_EditFavoriteDescription,
    FACS_OT_LoadFavorites,
    FACSProperties,
    FACS_MainProperties,
    FACS_PT_Panel
]

def register():
    global _first_run_popup_attempts
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.facs_main = PointerProperty(type=FACS_MainProperties)
    
    for category in FACS_ALL_CATEGORY_NAMES:
        setattr(FACS_MainProperties, f"show_{category.lower()}", BoolProperty(default=False))
    
    bpy.app.handlers.load_post.append(load_favorites_handler)

    _first_run_popup_attempts = 0
    if not has_seen_first_run_settings():
        try:
            if not bpy.app.timers.is_registered(show_first_run_settings_popup):
                bpy.app.timers.register(show_first_run_settings_popup, first_interval=0.75)
        except Exception as e:
            print(f"Error scheduling first-run settings popup: {str(e)}")

def unregister():
    if load_favorites_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_favorites_handler)

    try:
        if bpy.app.timers.is_registered(show_first_run_settings_popup):
            bpy.app.timers.unregister(show_first_run_settings_popup)
    except Exception:
        pass
    
    for category in FACS_ALL_CATEGORY_NAMES:
        if hasattr(FACS_MainProperties, f"show_{category.lower()}"):
            delattr(FACS_MainProperties, f"show_{category.lower()}")
    
    if hasattr(bpy.types.Scene, "facs_main"):
        del bpy.types.Scene.facs_main
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
