bl_info = {
    "name": "B UNicodes",
    "author": "Dinesh",
    "version": (1, 2, 0),
    "blender": (5, 1, 0),
    "description": "Access Unicode characters in Text Editor, VSE, and 3D Viewport.",
    "category": "3D Viewport, VSE, Text Editor",
}

import bpy
import unicodedata
import itertools

# ---------------------------------------------------------------------------
# Module-level cached data (built once at import, not on every panel redraw)
# ---------------------------------------------------------------------------

import json
import os

data_filepath = os.path.join(os.path.dirname(__file__), "unicode_data.json")
try:
    with open(data_filepath, "r", encoding="utf-8") as f:
        unicode_data = json.load(f)
    
    # Nested structure: group -> subgroup -> {char: tooltip}
    UNICODE_CATEGORIES = {}   # group -> [subgroup_name, ...]
    UNICODE_SUBGROUPS = {}    # "group::subgroup" -> [char, ...]
    UNICODE_TOOLTIPS = {}     # char -> tooltip

    for cat, subgroups in unicode_data.items():
        UNICODE_CATEGORIES[cat] = []
        for subgroup_name, chars_dict in subgroups.items():
            UNICODE_CATEGORIES[cat].append(subgroup_name)
            key = f"{cat}::{subgroup_name}"
            UNICODE_SUBGROUPS[key] = list(chars_dict.keys())
            UNICODE_TOOLTIPS.update(chars_dict)
except Exception as e:
    print(f"Error loading unicode_data.json: {e}")
    UNICODE_CATEGORIES = {"Symbols": ["symbols"]}
    UNICODE_SUBGROUPS = {"Symbols::symbols": []}
    UNICODE_TOOLTIPS = {}

def get_category_items(self, context):
    if not UNICODE_CATEGORIES:
        return [("Symbols", "Symbols", "")]
    return [(cat, cat, "") for cat in list(UNICODE_CATEGORIES.keys())]

# Pre-compute lowercase tooltips for ultra-fast C-level text searching
CACHED_LOWER_TOOLTIPS = {char: tooltip.lower() for char, tooltip in UNICODE_TOOLTIPS.items()}

def get_unicode_characters(settings):
    category = settings.active_category
    if category == "Recents":
        return list(settings.recent_chars)
    
    # Return all chars across all subgroups in this category
    chars = []
    for subgroup_name in UNICODE_CATEGORIES.get(category, []):
        key = f"{category}::{subgroup_name}"
        chars.extend(UNICODE_SUBGROUPS.get(key, []))
    return chars

_cached_search_term = None
_cached_search_results = []


def draw_char_grid(layout, chars, settings):
    """Draw a grid of unicode character buttons."""
    grid = layout.grid_flow(row_major=True, columns=5, align=True)
    for char in chars:
        tooltip = UNICODE_TOOLTIPS.get(char, char)
        if settings.copy_mode:
            op = grid.operator("unicode.copy_to_clipboard", text=char)
        else:
            op = grid.operator("text.insert_unicode", text=char)
        op.unicode_char = char
        op.tooltip = tooltip


def draw_header_controls(layout, settings):
    """Draw the shared header controls (copy mode, search, category)."""
    global _cached_search_term, _cached_search_results

    # Toggle for Copy Mode
    row = layout.row()
    if settings.copy_mode:
        row.prop(settings, "copy_mode", text="Copy Mode", icon='COPYDOWN')
    else:
        row.alert = True
        row.prop(settings, "copy_mode", text="Insert Mode", icon='EDITMODE_HLT')
    
    # Search bar
    layout.prop(settings, "search_filter", text="", icon='VIEWZOOM', placeholder="Search characters...")

    if not settings.search_filter:
        layout.prop(settings, "active_category", text="Category", icon='OUTLINER_COLLECTION')


def draw_search_results(layout, settings):
    """Draw search results as a flat grid."""
    global _cached_search_term, _cached_search_results

    search_term = settings.search_filter.strip().lower()
    if not search_term:
        return False

    if search_term != _cached_search_term:
        _cached_search_results = list(
            itertools.islice(
                (char for char, tooltip_lower in CACHED_LOWER_TOOLTIPS.items() if search_term in tooltip_lower),
                100
            )
        )
        _cached_search_term = search_term

    draw_char_grid(layout, _cached_search_results, settings)
    return True


def draw_recents(layout, settings):
    """Draw the Recents row at the bottom."""
    if settings.recent_chars:
        layout.separator()
        box = layout.box()
        box.label(text="Recents", icon='TIME')
        recent_grid = box.grid_flow(row_major=True, columns=8, align=True)
        for char in settings.recent_chars:
            tooltip = UNICODE_TOOLTIPS.get(char, char)
            if settings.copy_mode:
                op = recent_grid.operator("unicode.copy_to_clipboard", text=char)
            else:
                op = recent_grid.operator("text.insert_unicode", text=char)
            op.unicode_char = char
            op.tooltip = tooltip


# ---------------------------------------------------------------------------
# Parent panels (one per editor space)
# ---------------------------------------------------------------------------

class UnicodeCollectionPanelTextEditor(bpy.types.Panel):
    bl_label = "Unicode Collection"
    bl_idname = "TEXT_PT_unicode_collection"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Unicode'

    def draw(self, context):
        settings = context.scene.unicode_settings
        draw_header_controls(self.layout, settings)
        if draw_search_results(self.layout, settings):
            return
        draw_single_subgroup_inline(self.layout, settings)
        draw_recents(self.layout, settings)

class UnicodeCollectionPanelVSE(bpy.types.Panel):
    bl_label = "Unicode Collection"
    bl_idname = "VSE_PT_unicode_collection"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Unicode'

    def draw(self, context):
        settings = context.scene.unicode_settings
        draw_header_controls(self.layout, settings)
        if draw_search_results(self.layout, settings):
            return
        draw_single_subgroup_inline(self.layout, settings)
        draw_recents(self.layout, settings)

class UnicodeCollectionPanelViewport(bpy.types.Panel):
    bl_label = "Unicode Collection"
    bl_idname = "VIEW3D_PT_unicode_collection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unicode'

    def draw(self, context):
        settings = context.scene.unicode_settings
        draw_header_controls(self.layout, settings)
        if draw_search_results(self.layout, settings):
            return
        draw_single_subgroup_inline(self.layout, settings)
        draw_recents(self.layout, settings)


def draw_single_subgroup_inline(layout, settings):
    """For categories with only one subgroup, draw chars directly in the parent panel."""
    if settings.search_filter.strip():
        return
    category = settings.active_category
    subgroups = UNICODE_CATEGORIES.get(category, [])
    if len(subgroups) == 1:
        key = f"{category}::{subgroups[0]}"
        chars = UNICODE_SUBGROUPS.get(key, [])
        if chars:
            draw_char_grid(layout, chars, settings)


# ---------------------------------------------------------------------------
# Dynamically generated sub-panels (native Blender collapse/expand)
# ---------------------------------------------------------------------------

_dynamic_subpanel_classes = []

def _make_subpanel_draw(subgroup_key):
    """Create a draw method for a subgroup sub-panel."""
    def draw(self, context):
        settings = context.scene.unicode_settings
        chars = UNICODE_SUBGROUPS.get(subgroup_key, [])
        if chars:
            draw_char_grid(self.layout, chars, settings)
    return draw

def _make_subpanel_poll(category_name):
    """Only show the sub-panel when its parent category is active and not searching."""
    @classmethod
    def poll(cls, context):
        settings = context.scene.unicode_settings
        return settings.active_category == category_name and not settings.search_filter.strip()
    return poll

def _create_subpanel_classes():
    """Generate native Blender sub-panel classes for each subgroup under each editor."""
    global _dynamic_subpanel_classes
    _dynamic_subpanel_classes = []
    
    # Parent panel info for each editor
    editors = [
        ("TEXT", "TEXT_EDITOR", "TEXT_PT_unicode_collection"),
        ("VSE",  "SEQUENCE_EDITOR", "VSE_PT_unicode_collection"),
        ("V3D",  "VIEW_3D", "VIEW3D_PT_unicode_collection"),
    ]
    
    for cat_idx, (category, subgroups) in enumerate(UNICODE_CATEGORIES.items()):
        # Skip categories with only one subgroup – rendered inline by parent
        if len(subgroups) <= 1:
            continue
        for sub_idx, subgroup_name in enumerate(subgroups):
            key = f"{category}::{subgroup_name}"
            chars = UNICODE_SUBGROUPS.get(key, [])
            if not chars:
                continue
            
            label = subgroup_name.replace('-', ' ').title()
            
            for editor_prefix, space_type, parent_id in editors:
                import hashlib
                safe_cat = category.replace(' ', '').replace('&', 'n')
                safe_sub_raw = subgroup_name.replace(' ', '_').replace('-', '_').replace('&', 'n')
                
                # Blender allows max 63 characters for bl_idname.
                # len({editor_prefix}_PT_unicode_{safe_cat}_) is roughly 15 + len(safe_cat)
                base_name = f"{editor_prefix}_PT_unicode_{safe_cat}_"
                max_sub_len = 63 - len(base_name)
                
                if len(safe_sub_raw) > max_sub_len:
                    hash_str = hashlib.md5(subgroup_name.encode('utf-8')).hexdigest()[:6]
                    safe_sub = safe_sub_raw[:max_sub_len - 7] + "_" + hash_str
                else:
                    safe_sub = safe_sub_raw
                    
                idname = f"{base_name}{safe_sub}"
                
                # Sanitize to valid blender subset just in case
                import re
                idname = re.sub(r'[^A-Za-z0-9_]', '_', idname)

                # Create class dynamically using type()
                panel_cls = type(idname, (bpy.types.Panel,), {
                    'bl_label': label,
                    'bl_idname': idname,
                    'bl_space_type': space_type,
                    'bl_region_type': 'UI',
                    'bl_category': 'Unicode',
                    'bl_parent_id': parent_id,
                    'bl_options': {'DEFAULT_CLOSED'},
                    'bl_order': cat_idx * 100 + sub_idx,
                    'draw': _make_subpanel_draw(key),
                    'poll': _make_subpanel_poll(category),
                })
                
                _dynamic_subpanel_classes.append(panel_cls)


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class CopyUnicodeOperator(bpy.types.Operator):
    """Copy Unicode Character to Clipboard"""
    bl_idname = "unicode.copy_to_clipboard"
    bl_label = "Copy Unicode Character"

    unicode_char: bpy.props.StringProperty()
    tooltip: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        settings = context.scene.unicode_settings
        recents = settings.recent_chars
        recents = self.unicode_char + recents.replace(self.unicode_char, "")
        settings.recent_chars = recents[:25]

        context.window_manager.clipboard = self.unicode_char
        self.report({'INFO'}, f"Copied '{self.unicode_char}' to clipboard")
        return {'FINISHED'}

class InsertUnicodeOperator(bpy.types.Operator):
    bl_idname = "text.insert_unicode"
    bl_label = "Insert Unicode Character"

    unicode_char: bpy.props.StringProperty()
    tooltip: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        settings = context.scene.unicode_settings
        recents = settings.recent_chars
        recents = self.unicode_char + recents.replace(self.unicode_char, "")
        settings.recent_chars = recents[:25]

        space_type = context.space_data.type
        
        if space_type == 'TEXT_EDITOR':
            text = context.space_data.text
            if text:
                cursor_position = text.current_character
                current_line = text.current_line.body
                before_cursor = current_line[:cursor_position]
                after_cursor = current_line[cursor_position:]
                text.current_line.body = before_cursor + self.unicode_char + after_cursor
                text.current_character = cursor_position + len(self.unicode_char)
                self.report({'INFO'}, f"Inserted Unicode: {self.unicode_char}")
            else:
                self.report({'WARNING'}, "No active text block.")

        elif space_type == 'SEQUENCE_EDITOR':
            scene = context.scene
            sequence_editor = scene.sequence_editor
            if sequence_editor:
                strips = getattr(sequence_editor, "strips", getattr(sequence_editor, "sequences", []))
                selected_strips = [strip for strip in strips if strip.select and strip.type == 'TEXT']
                if selected_strips:
                    try:
                        target_region = next((r for r in context.area.regions if r.type == 'PREVIEW'), None)
                        if not target_region:
                            target_region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
                        if target_region:
                            with context.temp_override(area=context.area, region=target_region):
                                bpy.ops.sequencer.text_insert(string=self.unicode_char)
                        else:
                            bpy.ops.sequencer.text_insert(string=self.unicode_char)
                        self.report({'INFO'}, f"{self.unicode_char} inserted at cursor in Text strip: {selected_strips[0].name}")
                    except Exception as e:
                        print("Insert Unicode VSE Error:", e)
                        selected_strips[0].text += self.unicode_char
                        self.report({'INFO'}, f"{self.unicode_char} appended to Text strip: {selected_strips[0].name}")
                else:
                    self.report({'WARNING'}, "Please select a text strip in the VSE.")
        
        elif space_type == 'VIEW_3D':
            selected_objs = [obj for obj in context.selected_objects if obj.type == 'FONT']
            if selected_objs:
                text_obj = selected_objs[0]
                if context.object.mode == 'OBJECT':
                    text_obj.data.body += self.unicode_char
                    self.report({'INFO'}, f"{self.unicode_char} added to text object: {text_obj.name}")
                elif context.object.mode == 'EDIT':
                    try:
                        window_region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
                        if window_region:
                            with context.temp_override(area=context.area, region=window_region):
                                bpy.ops.font.text_insert(text=self.unicode_char)
                        else:
                            bpy.ops.font.text_insert(text=self.unicode_char)
                        self.report({'INFO'}, f"{self.unicode_char} inserted at cursor in text object: {text_obj.name}")
                    except Exception as e:
                        print("Insert Unicode 3D Error:", e)
                        self.report({'WARNING'}, "Could not insert at cursor in Edit Mode. Switch to Object mode to append.")
            else:
                self.report({'WARNING'}, "Please select a text object in the 3D View.")
        
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class UnicodeSettings(bpy.types.PropertyGroup):
    active_category: bpy.props.EnumProperty(
        name="Category",
        description="Select Unicode category",
        items=get_category_items
    )
    recent_chars: bpy.props.StringProperty(
        name="Recent Characters",
        default="",
    )
    copy_mode: bpy.props.BoolProperty(
        name="Copy Mode",
        description="Toggle between Copy and Insert modes",
        default=False,
    )
    search_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter unicode characters by name",
        default="",
        options={'TEXTEDIT_UPDATE'},
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_static_classes = (
    UnicodeSettings,
    UnicodeCollectionPanelTextEditor,
    UnicodeCollectionPanelVSE,
    UnicodeCollectionPanelViewport,
    InsertUnicodeOperator,
    CopyUnicodeOperator,
)

def register():
    for cls in _static_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.unicode_settings = bpy.props.PointerProperty(type=UnicodeSettings)
    
    # Generate and register dynamic sub-panels
    _create_subpanel_classes()
    for cls in _dynamic_subpanel_classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"B Unicode addon error registering class {cls.__name__}: {e}")

def unregister():
    # Unregister dynamic sub-panels first
    for cls in reversed(_dynamic_subpanel_classes):
        bpy.utils.unregister_class(cls)
    _dynamic_subpanel_classes.clear()
    
    del bpy.types.Scene.unicode_settings
    for cls in reversed(_static_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
