import bpy
import gpu
import blf
import time
from gpu_extras.batch import batch_for_shader
from collections import defaultdict
from functools import lru_cache

# Color schemes for different syntax elements in the minimap
SYNTAX_COLORS = {
    'plain': (0.75, 0.75, 0.75, 0.6), 'strings': (0.85, 0.75, 0.50, 0.8),
    'comments': (0.40, 0.40, 0.40, 0.6), 'numbers': (0.50, 0.75, 0.80, 0.9),
    'builtin': (0.85, 0.40, 0.45, 0.9), 'prepro': (0.55, 0.50, 0.85, 0.9),
    'special': (0.40, 0.60, 0.40, 0.9), 'reserved': (0.8, 0.8, 0.8, 0.9),
    'symbol': (1.0, 0.45, 0.3, 1.0),
}
HOVER_SYNTAX_COLORS = {}

# Sets of keywords and symbols for fast tokenization
BUILTIN = frozenset({'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try',
                    'except', 'import', 'from', 'return', 'break', 'continue',
                     'pass', 'with', 'as', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is'})
KEYWORDS = frozenset({'None', 'True', 'False'})
SYMBOLS = set("=:+-*/%&|^~<>!()[]{}.,")

# Global state dictionaries to manage minimap interaction
_drag_state = {'is_dragging': False, 'last_top': -1}
_hover_state = {'line_index': None, 'mouse_y': 0, 'last_mouse_x': 0, 'last_mouse_y': 0}
_perf_stats = {'draw_time': 0, 'cache_hits': 0, 'cache_misses': 0}

# -----------------------
# Cached helpers
# -----------------------


@lru_cache(maxsize=8)
def get_cached_shader(shader_type):
    return gpu.shader.from_builtin(shader_type)


@lru_cache(maxsize=8192)
def syntax_tokenize(line: str, for_hover_preview: bool):
    tokens = []
    i = 0
    line_len = len(line)

    while i < line_len:
        char = line[i]
        if char.isspace():
            i += 1
            continue

        start = i

        # Comments: Check for '#' and treat the rest of the line as a comment
        if char == '#':
            tokens.append((start, line_len, 'comments'))
            break

        # Strings: Check for single or double quotes
        if char in '"\'':
            quote = char
            i += 1
            while i < line_len:
                if line[i] == quote:
                    i += 1
                    break
                # Handle escaped characters within strings
                if line[i] == '\\' and i + 1 < line_len:
                    i += 2
                else:
                    i += 1
            tokens.append((start, i, 'strings'))
            continue

        # Numbers: Check for digits and decimals
        if char.isdigit():
            while i < line_len and (line[i].isdigit() or line[i] == '.'):
                i += 1
            tokens.append((start, i, 'numbers'))
            continue

        # Decorators: Check for '@' symbol
        if char == '@':
            while i < line_len and not line[i].isspace():
                i += 1
            tokens.append((start, i, 'prepro'))
            continue

        # Symbols: Check for a predefined set of symbols
        if char in SYMBOLS:
            # Use 'symbol' color for hover preview, 'plain' for minimap content
            token_type = 'symbol' if for_hover_preview else 'plain'
            while i < line_len and line[i] in SYMBOLS:
                i += 1
            tokens.append((start, i, token_type))
            continue

        # Identifiers and keywords: Check for letters and underscores
        if char.isalpha() or char == '_':
            while i < line_len and (line[i].isalnum() or line[i] == '_'):
                i += 1
            word = line[start:i]

            # Assign token type based on the word
            if word in {'def', 'class'}:
                token_type = 'special'
            elif word in BUILTIN:
                token_type = 'builtin'
            elif word in KEYWORDS:
                token_type = 'keywords'
            else:
                token_type = 'plain'

            tokens.append((start, i, token_type))
            continue

        # Move to the next character if none of the above conditions are met
        i += 1

    return tuple(tokens)  # Return an immutable tuple for safe caching


@lru_cache(maxsize=64)
def get_visible_range_cached(space_top: int, visible_lines: int, total_lines: int, dpi_factor: float, line_height_factor: float):
    lh = round(dpi_factor * line_height_factor)
    extra = max(4, visible_lines // 2)
    ext = total_lines + extra
    return {'extra': extra, 'extended_total': ext, 'line_height': lh}


@lru_cache(maxsize=256)
def get_hover_preview_data(text_name: str, hover_line_index: int, total_lines: int, text_version: int):
    preview_lines = min(12, total_lines)
    start_line = max(0, hover_line_index - preview_lines // 2)
    end_line = min(total_lines, start_line + preview_lines)

    # Adjust the range if it's too close to the end of the file
    if end_line - start_line < preview_lines and start_line > 0:
        start_line = max(0, end_line - preview_lines)
    return start_line, end_line

# -----------------------
# Helper functions
# -----------------------


def get_addon_prefs(context):
    from .. import TEXTIFY_preferences
    return context.preferences.addons[TEXTIFY_preferences.bl_idname].preferences


def get_dpi_factor(context):
    return context.preferences.system.dpi / 72.0


def get_text_editor_context():
    for area in bpy.context.screen.areas:
        if area.type == 'TEXT_EDITOR':
            space = area.spaces.active
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, space
    return None, None, None


def point_in_rect(x, y, rect):
    return rect['x'] <= x <= rect['x'] + rect['width'] and rect['y'] <= y <= rect['y'] + rect['height']


# -----------------------
# MinimapTextCache
# -----------------------

class MinimapTextCache:
    def __init__(self):
        self._text_signatures = {}

    def _get_text_signature(self, text):
        # Creates a signature for a text block to detect if it has changed.
        return (len(text.lines), getattr(text, "version", 0))

    def get_tokens(self, text, line_index, line_content, for_hover_preview=False):
        if for_hover_preview:
            return list(syntax_tokenize(line_content, True))

        num_lines = len(text.lines)
        if num_lines > 5000:
            return list(syntax_tokenize(line_content, False))

        return list(syntax_tokenize(line_content, False))

    def get_visible_range(self, space, total_lines, context):
        prefs = get_addon_prefs(context)
        dpi = get_dpi_factor(context)
        return get_visible_range_cached(space.top, space.visible_lines, total_lines, dpi, prefs.line_height_factor)

    def clear(self):
        self._text_signatures.clear()


_minimap_cache = MinimapTextCache()

# -----------------------
# Drawing helpers
# -----------------------


def draw_rectangles(rects_by_color):
    if not rects_by_color:
        return

    shader = get_cached_shader('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')

    for color, rects in rects_by_color.items():
        if not rects:
            continue
        coords = []
        for x, y, w, h in rects:
            coords.extend([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])

        if coords:
            # Create a list of triangle indices from the quad coordinates
            indices = [(i, i + 1, i + 2, i + 2, i + 3, i) for i in range(0, len(coords), 4)]
            tri_indices = [idx for quad in indices for idx in (
                (quad[0], quad[1], quad[2]), (quad[3], quad[4], quad[5]))]
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=tri_indices)
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)

    gpu.state.blend_set('NONE')


def draw_background(rect, color):
    shader = get_cached_shader('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    coords = [(rect['x'], rect['y']), (rect['x'] + rect['width'], rect['y']),
              (rect['x'] + rect['width'], rect['y'] + rect['height']),
              (rect['x'], rect['y'] + rect['height'])]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_border(rect, color, thickness=1):
    shader = get_cached_shader('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
    border_rects = [(x, y + h - thickness, w, thickness), (x, y, w, thickness),
                    (x, y, thickness, h), (x + w - thickness, y, thickness, h)]
    coords = []
    indices = []

    for i, (bx, by, bw, bh) in enumerate(border_rects):
        base_idx = i * 4
        coords.extend([(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh)])
        indices.extend([(base_idx, base_idx + 1, base_idx + 2),
                       (base_idx + 2, base_idx + 3, base_idx)])

    if coords:
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_minimap_content(rect, space, context, syntax_highlight=True):
    prefs = get_addon_prefs(context)
    lines = space.text.lines
    total = len(lines)
    if total == 0:
        return

    rects_by_color = defaultdict(list)
    base_y = rect['y'] + rect['height']
    cw = get_dpi_factor(context) * prefs.char_width_factor
    indent_factor = cw * 0.8
    rect_height = max(1, int(prefs.line_height_factor * 0.5))
    mc = int(rect['width'] / cw)

    # === FIT MODE & NORMAL MODE LINE HEIGHT LOGIC ===
    range_data_normal = _minimap_cache.get_visible_range(space, total, context)
    normal_lh = range_data_normal['line_height']
    natural_limit = int(rect['height'] / normal_lh)

    if prefs.minimap_fit:
        if total <= natural_limit:
            # Behave like normal mode (no stretch for short scripts)
            lh = normal_lh
            extra = range_data_normal['extra']
            ext = range_data_normal['extended_total']
            mh = lh * ext
            slide = int((mh - rect['height']) * space.top / max(1, ext -
                        space.visible_lines)) if mh > rect['height'] else 0
            skip_step = 1
        else:
            # True fit scaling for long scripts
            extra_blank = max(1, space.visible_lines // 2)
            total_with_extra = total + extra_blank
            lh = rect['height'] / max(1, total_with_extra)
            extra = extra_blank
            ext = total_with_extra
            slide = 0
            skip_step = max(1, int(2 / lh))
    else:
        # Normal mode
        lh = normal_lh
        extra = range_data_normal['extra']
        ext = range_data_normal['extended_total']
        mh = lh * ext
        slide = int((mh - rect['height']) * space.top / max(1, ext - space.visible_lines)) if mh > rect['height'] else 0
        skip_step = 1

    # === VISIBLE RANGE CALCULATION ===
    visible_buffer = lh * 2
    top = max(0, int((slide - visible_buffer) / lh))
    bot = min(ext, int((rect['height'] + slide + visible_buffer) / lh) + 1)

    if bot - top <= 0:
        return

    # === LINE DRAWING LOOP ===
    for i in range(top, min(bot, total), skip_step):
        line = lines[i].body
        if not line.strip():
            continue

        y = base_y - (lh * (i + 3)) + slide
        if y + rect_height < rect['y'] or y > rect['y'] + rect['height']:
            continue

        indent = len(line) - len(line.lstrip())
        content = line.lstrip()[:max(0, mc - indent)]
        x = rect['x'] + 4 + indent * indent_factor

        if not syntax_highlight:
            # Plain rectangle for performance
            content_width = len(content.rstrip()) * indent_factor
            if content_width > 0:
                rects_by_color[SYNTAX_COLORS['plain']].append((x, y, content_width, rect_height))
            continue

        # Syntax highlighting
        tokens = _minimap_cache.get_tokens(space.text, i, content, for_hover_preview=False)
        if not tokens:
            content_width = len(content.rstrip()) * indent_factor
            if content_width > 0:
                rects_by_color[SYNTAX_COLORS['plain']].append((x, y, content_width, rect_height))
            continue

        current_pos = 0
        current_x = x

        for start, end, token_type in tokens:
            # Draw plain text before token
            if current_pos < start:
                plain_text = content[current_pos:start]
                if plain_text:
                    width = len(plain_text) * indent_factor
                    rects_by_color[SYNTAX_COLORS['plain']].append((current_x, y, width, rect_height))
                current_x += len(plain_text) * indent_factor

            # Draw token
            token_text = content[start:end]
            if token_text:
                width = len(token_text) * indent_factor
                color = SYNTAX_COLORS.get(token_type, SYNTAX_COLORS['plain'])
                rects_by_color[color].append((current_x, y, width, rect_height))
            current_x += len(token_text) * indent_factor
            current_pos = end

        # Draw trailing plain text
        if current_pos < len(content):
            remaining = content[current_pos:].rstrip()
            if remaining:
                width = len(remaining) * indent_factor
                rects_by_color[SYNTAX_COLORS['plain']].append((current_x, y, width, rect_height))

    draw_rectangles(rects_by_color)


def draw_text_with_syntax(text, x, y, font_size, tokens, prefs, max_width, use_hover_colors=False):
    blf.size(0, font_size)
    if not text or not text.strip():
        return

    color_scheme = HOVER_SYNTAX_COLORS if use_hover_colors else SYNTAX_COLORS

    def clip_text_to_width(txt, remaining_width):
        if remaining_width <= 0:
            return ""
        test_width = blf.dimensions(0, txt)[0]
        if test_width <= remaining_width:
            return txt
        # Binary search to find max fitting substring
        left, right, result = 0, len(txt), ""
        while left <= right:
            mid = (left + right) // 2
            test_txt = txt[:mid]
            if blf.dimensions(0, test_txt)[0] <= remaining_width:
                result = test_txt
                left = mid + 1
            else:
                right = mid - 1
        return result

    available_width = max_width

    if not tokens:
        clipped_text = clip_text_to_width(text.rstrip(), available_width)
        if clipped_text:
            blf.color(0, *color_scheme.get('plain', SYNTAX_COLORS['plain']))
            blf.position(0, x, y, 0)
            blf.draw(0, clipped_text)
        return

    current_pos = 0
    text_x = x

    for start, end, token_type in tokens:
        if available_width <= 0:
            break

        # Draw plain text before the token
        if current_pos < start:
            plain_text = text[current_pos:start]
            if plain_text:
                clipped_plain = clip_text_to_width(plain_text, available_width)
                if clipped_plain:
                    blf.color(0, *color_scheme.get('plain', SYNTAX_COLORS['plain']))
                    blf.position(0, text_x, y, 0)
                    blf.draw(0, clipped_plain)
                    text_width = blf.dimensions(0, clipped_plain)[0]
                    text_x += text_width
                    available_width -= text_width
                    if len(clipped_plain) < len(plain_text):
                        return

        if available_width <= 0:
            break

        # Draw the token's text
        token_text = text[start:end]
        if token_text:
            clipped_token = clip_text_to_width(token_text, available_width)
            if clipped_token:
                color = color_scheme.get(token_type, color_scheme.get('plain', SYNTAX_COLORS['plain']))
                blf.color(0, *color)
                blf.position(0, text_x, y, 0)
                blf.draw(0, clipped_token)
                text_width = blf.dimensions(0, clipped_token)[0]
                text_x += text_width
                available_width -= text_width
                if len(clipped_token) < len(token_text):
                    return

        current_pos = end

    # Draw any remaining text at the end
    if current_pos < len(text) and available_width > 0:
        remaining_text = text[current_pos:].rstrip()
        if remaining_text:
            clipped_remaining = clip_text_to_width(remaining_text, available_width)
            if clipped_remaining:
                blf.color(0, *color_scheme.get('plain', SYNTAX_COLORS['plain']))
                blf.position(0, text_x, y, 0)
                blf.draw(0, clipped_remaining)


def draw_hover_preview(rect, space, context, hover_line_index):
    if _drag_state.get('is_dragging') or hover_line_index is None or not space.text:
        return

    lines = space.text.lines
    total_lines = len(lines)
    if hover_line_index >= total_lines:
        return

    text_name = space.text.name
    text_version = getattr(space.text, "version", 0)

    # Get the lines to show from the cached helper function
    start_line, end_line = get_hover_preview_data(text_name, hover_line_index, total_lines, text_version)

    theme = context.preferences.themes[0] if context.preferences.themes else None
    bg_color = (*theme.text_editor.space.back, 1.0) if theme else (0.08, 0.08, 0.08, 0.95)

    prefs = get_addon_prefs(context)
    dpi = get_dpi_factor(context)
    font_size = int(12 * dpi)
    line_height = int(font_size * 1.4)
    content_padding = 5

    # panel height = lines * line_height + 2 * padding
    panel_height = (end_line - start_line) * line_height + (content_padding * 2)
    panel_width  = int(prefs.hover_preview_width * dpi)

    panel_x = rect['x'] - panel_width - 15
    panel_y = max(15, min(_hover_state['mouse_y'] - panel_height // 2,
                          context.region.height - panel_height - 15))
    if panel_x < 0:
        return

    panel_rect = {'x': panel_x, 'y': panel_y, 'width': panel_width, 'height': panel_height}
    draw_background(panel_rect, bg_color)
    border_color = (bg_color[0] + 0.2, bg_color[1] + 0.2, bg_color[2] + 0.2, 0.8)
    draw_border(panel_rect, border_color, thickness=1)

    content_area = {
        'x': panel_x + content_padding,
        'y': panel_y + content_padding,
        'width': panel_width - (content_padding * 2),
        'height': panel_height - (content_padding * 2)
    }

    blf.size(0, font_size)

    # total height occupied by code lines
    lines_block_height = (end_line - start_line) * line_height

    # available content height inside the panel
    available_height = panel_height - (content_padding * 2)

    # extra space left after drawing all lines
    extra_space = max(0, available_height - lines_block_height)

    # starting Y (so top padding = bottom padding = content_padding + half of extra_space)
    start_y = panel_y + panel_height - content_padding - (extra_space // 2)

    for i in range(start_line, end_line):
        line_content = lines[i].body
        baseline_fix = 2   # tweak as needed
        y_pos = start_y - ((i - start_line + 1) * line_height) + baseline_fix

        # Draw line number
        line_num = str(i + 1).rjust(4)
        blf.color(0, 0.5, 0.5, 0.5, 1.0)
        blf.position(0, content_area['x'], y_pos, 0)
        blf.draw(0, line_num)

        # Draw the code line with syntax highlighting
        if line_content.strip():
            # Dynamically calculate the code_x and available_width
            line_num_width = blf.dimensions(0, line_num)[0]
            code_x = content_area['x'] + line_num_width + 10 # 10 is the padding between number and text
            available_width = content_area['width'] - line_num_width - 10

            tokens = list(syntax_tokenize(line_content, True))
            draw_text_with_syntax(line_content, code_x, y_pos, font_size, tokens,
                                  get_addon_prefs(context), available_width, use_hover_colors=True)


def get_minimap_rect(region, context):
    prefs = get_addon_prefs(context)
    dpi = get_dpi_factor(context)
    w = round(dpi * prefs.minimap_width)
    x = region.width - w - round(dpi * prefs.scrollbar_width)
    return {'x': x, 'y': 0, 'width': w, 'height': region.height}


def get_viewport_rect(rect, space, total, context):
    if total == 0:
        return None

    range_data = _minimap_cache.get_visible_range(space, total, context)
    lh = range_data['line_height']
    extra = range_data['extra']
    ext = range_data['extended_total']
    vis = space.visible_lines

    mh = lh * ext
    slide = int((mh - rect['height']) * space.top / max(1, ext - vis)) if mh > rect['height'] else 0

    viewport_start = lh * space.top
    viewport_end = lh * (space.top + vis)
    top_y = rect['height'] - viewport_start + slide
    bot_y = rect['height'] - viewport_end + slide

    top_y = max(-lh, min(rect['height'] + lh, top_y))
    bot_y = max(-lh, min(rect['height'] + lh, bot_y))
    height = max(0, top_y - bot_y)

    return {'x': rect['x'], 'y': bot_y, 'width': rect['width'], 'height': height, 'slide': slide} if height > 0 else None


def draw_minimap():
    context = bpy.context
    try:
        prefs = get_addon_prefs(context)
    except KeyError:
        return

    if not prefs.enable_minimap:
        return

    area, region, space = get_text_editor_context()
    if not area or not region or not space or not space.text:
        return

    rect = get_minimap_rect(region, context)
    if not rect:
        return

    total_lines = len(space.text.lines)

    # Draw the minimap content
    draw_background(rect, prefs.background_color)

    # Disable syntax highlighting if file is too large
    highlight_enabled = total_lines <= prefs.max_file_size

    draw_minimap_content(
        rect, space, context,
        syntax_highlight=highlight_enabled
    )

    # Draw viewport outline
    vr = get_viewport_rect(rect, space, total_lines, context)
    if vr:
        draw_rectangles({prefs.viewport_color: [(vr['x'], vr['y'], vr['width'], vr['height'])]})

    # Hover preview
    if prefs.enable_hover_preview and _hover_state['line_index'] is not None:
        draw_hover_preview(rect, space, context, _hover_state['line_index'])


def get_hovered_line_index(rect, space, context, mouse_x, mouse_y):
    if not point_in_rect(mouse_x, mouse_y, rect) or not space.text:
        return None

    total = len(space.text.lines)
    if total == 0:
        return None

    prefs = get_addon_prefs(context)
    if prefs.minimap_fit:
        line_height = rect['height'] / max(1, total)
        hover_line = int((rect['y'] + rect['height'] - mouse_y) / line_height)
        return max(0, min(total - 1, hover_line))
    else:
        range_data = _minimap_cache.get_visible_range(space, total, context)
        lh = range_data['line_height']
        ext = range_data['extended_total']
        slide = int(max(0, lh * ext - rect['height']) * space.top / ext) if ext > 0 else 0
        calculated_line = int((rect['y'] + rect['height'] - mouse_y + slide) / lh) - 3
        top = max(0, int(slide / lh))
        bot = min(ext, int((rect['height'] + slide) / lh))
        if top <= calculated_line < min(bot, total) and 0 <= calculated_line < total:
            return calculated_line
    return None


# -----------------------
# Operators
# -----------------------

class MINIMAP_OT_mouse_move(bpy.types.Operator):
    bl_idname = "minimap.mouse_move"
    bl_label = "Minimap Mouse Move"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return (prefs.enable_minimap and
                context.space_data and
                context.space_data.type == 'TEXT_EDITOR' and
                context.space_data.text is not None)

    def invoke(self, context, event):
        if _drag_state['is_dragging']:
            return {'PASS_THROUGH'}

        area, region, space = get_text_editor_context()
        if not area or not region or not space or not space.text:
            return {'PASS_THROUGH'}

        rect = get_minimap_rect(region, context)
        if not rect:
            return {'PASS_THROUGH'}

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        _hover_state.update({'mouse_y': mouse_y, 'last_mouse_x': mouse_x, 'last_mouse_y': mouse_y})

        # Check if the mouse is inside the minimap rect
        if point_in_rect(mouse_x, mouse_y, rect):
            new_hover_line = get_hovered_line_index(rect, space, context, mouse_x, mouse_y)
            if new_hover_line != _hover_state['line_index']:
                _hover_state['line_index'] = new_hover_line
                area.tag_redraw()
            context.window.cursor_set('DEFAULT')
        else:
            # Clear hover state if mouse moves out of the minimap
            if _hover_state['line_index'] is not None:
                _hover_state['line_index'] = None
                area.tag_redraw()

        return {'PASS_THROUGH'}


class MINIMAP_OT_minimap_drag(bpy.types.Operator):
    bl_idname = "minimap.drag"
    bl_label = "Minimap Drag Handler"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_prefs(context)
        return (prefs.enable_minimap and
                context.space_data and
                context.space_data.type == 'TEXT_EDITOR' and
                context.space_data.text is not None)

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE' and _drag_state['is_dragging']:
            area, region, space = get_text_editor_context()
            if not area or not region or not space or not space.text:
                return {'CANCELLED'}

            rect = get_minimap_rect(region, context)
            if not rect:
                return {'CANCELLED'}

            prefs = get_addon_prefs(context)
            total = len(space.text.lines)

            if prefs.minimap_fit:
                # Extra blank space after the file end
                extra_blank = max(1, space.visible_lines // 2)
                total_with_extra = total + extra_blank

                # Fit mapping uses total_with_extra so minimap includes the blank space.
                line_height = rect['height'] / max(1, total_with_extra)
                mouse_y = event.mouse_region_y
                target_line = int((rect['y'] + rect['height'] - mouse_y) / line_height) - (space.visible_lines // 2)
                new_top = max(0, min(target_line, total_with_extra - space.visible_lines))
            else:
                # Normal mode: compute slide using the *actual* scrollable range
                vr = get_viewport_rect(rect, space, total, context)
                if not vr:
                    return {'CANCELLED'}
                range_data = _minimap_cache.get_visible_range(space, total, context)
                lh = range_data['line_height']
                extra = range_data['extra']
                ext = range_data['extended_total']

                mh = lh * ext
                denom = max(1, total - space.visible_lines)
                if mh > rect['height'] and denom > 0:
                    current_slide = int((mh - rect['height']) * space.top / denom)
                else:
                    current_slide = 0

                viewport_center_y = vr['y'] + vr['height'] / 2
                mouse_y = event.mouse_region_y

                delta_y = viewport_center_y - mouse_y
                lines_to_move = delta_y / lh if lh > 0 else 0
                new_top = max(0, min(space.top + round(lines_to_move), max(0, total - space.visible_lines + extra)))

            if new_top != _drag_state['last_top']:
                space.top = new_top
                _drag_state['last_top'] = new_top
                area.tag_redraw()

            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            _drag_state['is_dragging'] = False
            context.window.cursor_set('DEFAULT')
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            _drag_state['is_dragging'] = False
            context.window.cursor_set('DEFAULT')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        area, region, space = get_text_editor_context()
        if not area or not region or not space or not space.text:
            return {'PASS_THROUGH'}

        rect = get_minimap_rect(region, context)
        if not rect:
            return {'PASS_THROUGH'}

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        total = len(space.text.lines)
        prefs = get_addon_prefs(context)

        vr = get_viewport_rect(rect, space, total, context)

        # Start dragging if clicking the viewport rectangle
        if vr and point_in_rect(mouse_x, mouse_y, vr):
            _drag_state['is_dragging'] = True
            _drag_state['last_top'] = space.top
            context.window_manager.modal_handler_add(self)
            context.window.cursor_set('HAND')
            return {'RUNNING_MODAL'}

        # Click on minimap -> jump to that area
        if point_in_rect(mouse_x, mouse_y, rect) and total > 0:
            if prefs.minimap_fit:
                extra_blank = max(1, space.visible_lines // 2)
                total_with_extra = total + extra_blank
                line_height = rect['height'] / max(1, total_with_extra)
                click_y = rect['y'] + rect['height'] - mouse_y
                target_line = int(click_y / line_height) - (space.visible_lines // 2)
                space.top = max(0, min(target_line, total_with_extra - space.visible_lines))
            else:
                # Normal mode: use slide computed relative to actual scrollable range
                range_data = _minimap_cache.get_visible_range(space, total, context)
                lh = range_data['line_height']
                ext = range_data['extended_total']
                mh = lh * ext
                denom = max(1, total - space.visible_lines)
                slide = int((mh - rect['height']) * space.top / denom) if (mh > rect['height'] and denom > 0) else 0
                click_y = rect['height'] - mouse_y + rect['y']
                target_line = int((click_y + slide) / lh) - 3
                space.top = max(0, min(target_line, max(0, total - space.visible_lines)))
            area.tag_redraw()
            return {'FINISHED'}

        return {'PASS_THROUGH'}


def register_draw_callback():
    unregister_minimap()
    handler = bpy.types.SpaceTextEditor.draw_handler_add(
        draw_minimap, (), 'WINDOW', 'POST_PIXEL')
    setattr(bpy.types.SpaceTextEditor, "_minimap_draw_handler", handler)


def unregister_minimap():
    if hasattr(bpy.types.SpaceTextEditor, "_minimap_draw_handler"):
        bpy.types.SpaceTextEditor.draw_handler_remove(
            getattr(bpy.types.SpaceTextEditor, "_minimap_draw_handler"), 'WINDOW')
        delattr(bpy.types.SpaceTextEditor, "_minimap_draw_handler")


def update_hover_syntax_colors_from_theme():
    global HOVER_SYNTAX_COLORS
    prefs = bpy.context.preferences
    theme = prefs.themes[0] if prefs.themes else None
    if not theme:
        HOVER_SYNTAX_COLORS = {
            'plain': (0.95, 0.95, 0.95, 1.0), 'strings': (0.79, 0.66, 0.17, 1.0),
            'comments': (0.70, 0.85, 0.70, 1.0), 'numbers': (0.065, 0.70, 0.80, 0.9),
            'builtin': (0.902, 0.180, 0.404, 1.0), 'prepro': (0.85, 0.75, 1.0, 1.0),
            'reserved': (0.8, 0.8, 0.8, 1.0), 'special': (0.40, 0.60, 0.25, 1.0),
            'symbol': (0.8, 0.8, 0.8, 1.0),
        }
        return

    text_theme = theme.text_editor
    HOVER_SYNTAX_COLORS = {
        'plain': (*text_theme.space.text, 1.0), 'strings': (*text_theme.syntax_string, 1.0),
        'comments': (*text_theme.syntax_comment, 1.0), 'numbers': (*text_theme.syntax_numbers, 1.0),
        'builtin': (*text_theme.syntax_builtin, 1.0), 'prepro': (*text_theme.syntax_preprocessor, 1.0),
        'keywords': (*text_theme.syntax_numbers, 1.0), 'special': (*text_theme.syntax_special, 1.0),
        'symbol': (*text_theme.syntax_symbols, 1.0),
    }


classes = (MINIMAP_OT_mouse_move, MINIMAP_OT_minimap_drag)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    update_hover_syntax_colors_from_theme()
    # Register draw callback shortly after enable to avoid issues with context
    bpy.app.timers.register(lambda: register_draw_callback() or None, first_interval=0.1)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Text Generic', space_type='TEXT_EDITOR')
        km.keymap_items.new('minimap.drag', 'LEFTMOUSE', 'PRESS')
        km.keymap_items.new('minimap.mouse_move', 'MOUSEMOVE', 'ANY', head=True)


def unregister():
    global _hover_state, _drag_state, _perf_stats

    # Clear lru_cache caches explicitly to free memory
    try:
        get_cached_shader.cache_clear()
    except Exception:
        pass
    try:
        syntax_tokenize.cache_clear()
    except Exception:
        pass
    try:
        get_visible_range_cached.cache_clear()
    except Exception:
        pass
    try:
        get_hover_preview_data.cache_clear()
    except Exception:
        pass

    unregister_minimap()
    _minimap_cache.clear()

    # Reset global state to initial values
    _hover_state = {'line_index': None, 'mouse_y': 0, 'last_mouse_x': 0, 'last_mouse_y': 0}
    _drag_state = {'is_dragging': False, 'last_top': -1}
    _perf_stats = {'draw_time': 0, 'cache_hits': 0, 'cache_misses': 0}

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    # Remove the keymap items
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        for km in wm.keyconfigs.addon.keymaps:
            if km.name == 'Text Generic':
                for kmi in list(km.keymap_items):
                    if kmi.idname in ('minimap.drag', 'minimap.mouse_move'):
                        km.keymap_items.remove(kmi)
                break
