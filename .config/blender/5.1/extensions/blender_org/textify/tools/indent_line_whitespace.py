# Original script credit for initial concepts: https://github.com/tin2tin/CodeEditor/blob/master/code_editor.py

import bpy
import blf
from gpu import state
from gpu.shader import from_builtin
from gpu_extras.batch import batch_for_shader
from collections import deque, defaultdict


# --- GPU Drawing Utilities ---
sh_2d = from_builtin('UNIFORM_COLOR')


def get_addon_prefs(context):
    from .. import TEXTIFY_preferences
    return context.preferences.addons[TEXTIFY_preferences.bl_idname].preferences


def draw_lines_2d(seq, color):
    batch = batch_for_shader(sh_2d, 'LINES', {'pos': seq})
    sh_2d.bind()
    sh_2d.uniform_float("color", [*color])
    batch.draw(sh_2d)


# --- UI Metrics ---
def get_widget_unit(context):
    system = context.preferences.system
    pixel_size = system.pixel_size
    dpi_scale = pixel_size * system.dpi
    return int((dpi_scale * 20 + 36) / 72 + (2 * (pixel_size - dpi_scale // 72)))


def get_character_width_and_offset(space_data, text_data):
    char_width = 0
    x_offset = 0
    if text_data and text_data.lines:
        for idx, line in enumerate(text_data.lines):
            if line.body:
                location_from_cursor = space_data.region_location_from_cursor
                x_offset = location_from_cursor(idx, 0)[0]
                char_width = location_from_cursor(idx, 1)[0] - x_offset
                break
    if not char_width:
        x_offset = get_widget_unit(bpy.context) // 2
        char_width = round(blf.dimensions(1, "T")[0])
    return char_width, x_offset


# --- Overlay Data Cache per Text Data-Block ---
class TextDataOverlayCache:
    def __init__(self, text_data_block):
        self.text_data_block = text_data_block
        self.indents = []
        self.indent_blocks = defaultdict(list)


_text_overlay_cache = {}


def get_text_data_cache(text_data_block):
    if text_data_block.name not in _text_overlay_cache:
        _text_overlay_cache[text_data_block.name] = TextDataOverlayCache(text_data_block)
    return _text_overlay_cache[text_data_block.name]


def cleanup_text_overlay_cache():
    # Remove cache entries for text data-blocks that no longer exist
    keys_to_remove = [key for key in _text_overlay_cache if key not in bpy.data.texts]
    for key in keys_to_remove:
        del _text_overlay_cache[key]


def calculate_indent_blocks_and_lines(text_lines, tab_width):
    indent_blocks = defaultdict(list)
    indent_stack = [(0, -1)]  # (indent_level, start_line_idx)

    line_indents = []
    prev_non_blank_indent = 0
    for line in text_lines:
        stripped_line = line.body.lstrip()
        if stripped_line:
            current_line_indent = (len(line.body) - len(stripped_line)) // tab_width
            line_indents.append(current_line_indent)
            prev_non_blank_indent = current_line_indent
        else:
            line_indents.append(prev_non_blank_indent)  # Blank lines inherit indent from last non-blank line

    for i, current_level in enumerate(line_indents):
        # Close blocks that are at a higher indent level than the current line
        while indent_stack and indent_stack[-1][0] > current_level:
            level_to_close, start_line = indent_stack.pop()
            indent_blocks[level_to_close].append((start_line, i - 1))

        # Start a new block if the current level is higher than the top of the stack
        if not indent_stack or indent_stack[-1][0] < current_level:
            indent_stack.append((current_level, i))

    # Close any remaining open blocks after iterating through all lines
    while indent_stack:
        level_to_close, start_line = indent_stack.pop()
        if level_to_close > 0:  # Don't create blocks for level 0 (no indent)
            indent_blocks[level_to_close].append((start_line, len(text_lines) - 1))

    return indent_blocks, line_indents


# --- Main Drawing Function ---
def draw_text_editor_overlay(area, context):
    if not hasattr(context, 'space_data') or not isinstance(context.space_data, bpy.types.SpaceTextEditor):
        return
    if not context.space_data.text:
        return
    if not isinstance(area, bpy.types.Area) or area.type != 'TEXT_EDITOR':
        return
    space_data = context.space_data

    prefs = get_addon_prefs(context)

    current_text_data_block = space_data.text
    region = context.region
    text_data_cache = get_text_data_cache(current_text_data_block)

    widget_unit = get_widget_unit(context)
    region_height = region.height
    char_width, x_offset_text_start = get_character_width_and_offset(space_data, current_text_data_block)

    line_number_area_width = space_data.show_line_numbers and len(repr(len(current_text_data_block.lines))) + 2
    text_area_x_start = char_width
    if space_data.show_line_numbers:
        text_area_x_start += char_width * line_number_area_width

    line_height = int((widget_unit * space_data.font_size // 20) * 1.3)
    top_visible_line_idx = space_data.top
    tab_width = space_data.tab_width
    indent_pixel_width = char_width * tab_width

    # Get text color from the active theme's text editor settings
    current_theme_name = context.preferences.themes.items()[0][0]
    text_editor_theme = context.preferences.themes[current_theme_name].text_editor
    plain_text_rgb_color = text_editor_theme.space.text

    visible_lines_count = space_data.visible_lines
    bottom_visible_line_idx = top_visible_line_idx + visible_lines_count

    state.blend_set("ALPHA")
    state.line_width_set(1.0)

    # --- Draw Indent Guides ---
    if prefs.enable_indent_guides:
        # Recalculate indents only if the number of lines changes or cache is empty
        if not text_data_cache.indent_blocks or len(text_data_cache.indents) != len(current_text_data_block.lines):
            text_data_cache.indent_blocks, text_data_cache.indents = \
                calculate_indent_blocks_and_lines(current_text_data_block.lines, tab_width)

        line_coordinates = deque()
        indent_guide_transparency = 0.15
        line_color_with_alpha = (*plain_text_rgb_color, indent_guide_transparency)

        for level in sorted(text_data_cache.indent_blocks.keys()):
            if level > 0:
                x_coord = x_offset_text_start + indent_pixel_width * (level - 1)

                if x_coord >= text_area_x_start:  # Only draw if guide is visible within text area
                    for block_start_line, block_end_line in text_data_cache.indent_blocks[level]:
                        # Clamp block lines to visible area
                        draw_start_line = max(block_start_line, top_visible_line_idx)
                        draw_end_line = min(block_end_line, bottom_visible_line_idx - 1)

                        if draw_start_line <= draw_end_line:
                            y_top = region_height - line_height * (draw_start_line - top_visible_line_idx)
                            y_bottom = region_height - line_height * (draw_end_line - top_visible_line_idx + 1)

                            # Ensure coordinates are within region bounds before adding
                            if y_top > 0 and y_bottom < region_height:
                                line_coordinates.extend(((x_coord, y_top), (x_coord, y_bottom)))

        draw_lines_2d(line_coordinates, line_color_with_alpha)

    # --- Draw Whitespace Characters ---
    if prefs.enable_whitespace_chars:
        whitespace_char_transparency = 0.12
        whitespace_color = (*plain_text_rgb_color, whitespace_char_transparency)

        # Calculate character indices for the visible portion of the line based on horizontal scroll
        st_left_char_idx = (text_area_x_start // char_width) - (x_offset_text_start // char_width)
        if st_left_char_idx < 0:  # Ensure start index is not negative
            st_left_char_idx = 0
        cend_char_idx = (region.width - text_area_x_start) // char_width

        whitespace_lines_to_draw = []
        for line_obj in current_text_data_block.lines[top_visible_line_idx:bottom_visible_line_idx]:
            temp_line_chars = []
            tab_pixel_offset = 0  # Accounts for visual width difference of tabs (variable width)
            for char_idx, char in enumerate(line_obj.body):
                if char_idx < st_left_char_idx:
                    if char == "\t":
                        tab_pixel_offset += tab_width - (char_idx % tab_width)
                    temp_line_chars.append(" ")  # Placeholder for non-visible leading chars
                    continue

                if char == "\t":
                    remaining_tab_spaces = tab_width - ((char_idx + tab_pixel_offset) % tab_width) - 1
                    temp_line_chars.append(" " * remaining_tab_spaces + "→")
                    tab_pixel_offset += remaining_tab_spaces
                elif char == " ":
                    temp_line_chars.append("·")
                else:
                    temp_line_chars.append(" ")  # Placeholder for non-whitespace characters

            whitespace_lines_to_draw.append("".join(temp_line_chars))

        blf.color(1, *whitespace_color)

        current_y_pos = region_height - (line_height * 0.8)
        for ws_line_str in whitespace_lines_to_draw:
            if ws_line_str:
                blf.position(1, text_area_x_start, current_y_pos, 0)
                # Draw only the portion of the generated string that is visible
                blf.draw(1, ws_line_str[st_left_char_idx: st_left_char_idx + cend_char_idx + 1])
            current_y_pos -= line_height

    state.line_width_set(1.0)
    state.blend_set("NONE")
    blf.rotation(0, 0)
    blf.disable(0, blf.ROTATION)


_area_draw_handlers = {}  # Stores active draw handlers by area pointer
_is_managing_areas = False  # Flag to prevent multiple timer registrations


def unregister_area_draw_handler(area_ptr):
    """Unregisters the draw handler for a specific Text Editor area pointer if it exists."""
    if area_ptr in _area_draw_handlers:
        handler = _area_draw_handlers[area_ptr]
        try:
            bpy.types.SpaceTextEditor.draw_handler_remove(handler, 'WINDOW')
        except Exception:
            # It may have already been removed, so we just pass
            pass
        finally:
            # Always remove from our tracking dict
            del _area_draw_handlers[area_ptr]


def register_area_draw_handler(area):
    """Registers a draw handler for a specific Text Editor area's main region."""
    ptr = area.as_pointer()
    if ptr in _area_draw_handlers:
        # If a handler is already tracked for this area, no need to do anything
        return

    try:
        handler = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_text_editor_overlay, (area, bpy.context), 'WINDOW', 'POST_PIXEL'
        )
        _area_draw_handlers[ptr] = handler
    except Exception as e:
        print(f"Failed to register draw handler for area {ptr}: {e}")


def manage_text_editor_areas():
    """
    Called periodically by a timer. It scans for existing Text Editor areas
    to register draw handlers and unregisters handlers for closed areas.
    """
    global _is_managing_areas
    if not bpy.context or not hasattr(bpy.context, 'window_manager'):
        _is_managing_areas = False
        return None  # Stop the timer if context is invalid

    try:
        cleanup_text_overlay_cache()

        current_area_pointers = set()
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                ptr = area.as_pointer()
                current_area_pointers.add(ptr)
                if area.type == 'TEXT_EDITOR':
                    register_area_draw_handler(area)

        # Unregister handlers for areas that no longer exist
        for ptr in list(_area_draw_handlers.keys()):
            if ptr not in current_area_pointers:
                unregister_area_draw_handler(ptr)

    except Exception as e:
        print(f"Error in manage_text_editor_areas: {e}")
        _is_managing_areas = False
        return None

    return 5.0


def cleanup_all_handlers():
    """Force cleanup of all draw handlers by iterating over our tracked dictionary."""
    global _area_draw_handlers
    # Iterate over a copy of the keys to allow modification of the dictionary during cleanup
    for ptr in list(_area_draw_handlers.keys()):
        unregister_area_draw_handler(ptr)


def register():
    global _is_managing_areas

    # Always clean up any existing handlers first
    cleanup_all_handlers()

    if not _is_managing_areas:
        bpy.app.timers.register(manage_text_editor_areas, first_interval=0.1)
        _is_managing_areas = True


def unregister():
    global _is_managing_areas

    # The most important part: remove all handlers and stop the timer
    cleanup_all_handlers()

    if _is_managing_areas:
        if manage_text_editor_areas in bpy.app.timers:
            bpy.app.timers.unregister(manage_text_editor_areas)
        _is_managing_areas = False