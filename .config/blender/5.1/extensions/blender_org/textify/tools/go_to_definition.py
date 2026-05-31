import bpy
from bpy.types import Operator
from pathlib import Path

# Global cache for Jedi results to improve performance
_jedi_cache = {}
_jedi_module = None


def get_addon_prefs(context):
    from .. import TEXTIFY_preferences
    return context.preferences.addons[TEXTIFY_preferences.bl_idname].preferences


def get_jedi_module():
    """Lazy import of Jedi module with caching"""
    global _jedi_module
    if _jedi_module is None:
        try:
            import jedi
            _jedi_module = jedi
        except ImportError:
            raise ImportError("Jedi module not found. Please install it with: pip install jedi")
    return _jedi_module


class TEXTIFY_OT_goto_definition(Operator):
    bl_idname = "textify.goto_definition"
    bl_label = "Go to Definition"
    bl_description = "Jump to the definition of the symbol under cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area and
                context.area.type == 'TEXT_EDITOR' and
                context.edit_text and
                context.edit_text.current_line)


    def execute(self, context):
        text = context.edit_text
        if not text:
            self.report({'WARNING'}, "No text editor active")
            return {'CANCELLED'}

        # Get current cursor position
        current_line = text.current_line_index
        current_character = text.current_character

        # Get the source code
        source = text.as_string()

        # Create cache key
        cache_key = (hash(source), current_line, current_character)

        # Check cache first
        if cache_key in _jedi_cache:
            definitions = _jedi_cache[cache_key]
        else:
            try:
                # Import Jedi lazily
                jedi = get_jedi_module()

                # Create Jedi script
                script = jedi.Script(code=source)

                # Get definitions
                definitions = script.goto(line=current_line + 1, column=current_character)

                # Cache the result
                _jedi_cache[cache_key] = definitions

            except ImportError as e:
                self.report({'ERROR'}, str(e))
                return {'CANCELLED'}
            except Exception as e:
                self.report({'WARNING'}, f"Jedi error: {str(e)}")
                return {'CANCELLED'}

        if not definitions:
            # Try to get names/references if no definitions found
            try:
                jedi = get_jedi_module()
                script = jedi.Script(code=source)
                definitions = script.goto(line=current_line + 1, column=current_character)

                if not definitions:
                    self.report({'INFO'}, "No definition found for symbol under cursor")
                    return {'CANCELLED'}
            except Exception as e:
                self.report({'INFO'}, "No definition found for symbol under cursor")
                return {'CANCELLED'}

        # Get the first definition
        definition = definitions[0]

        try:
            # Determine filepath for jump_to_file_at_point
            if definition.module_path is None:
                # Definition is in current file (unsaved text)
                if text.filepath:
                    filepath = text.filepath
                else:
                    # For unsaved text, save it temporarily or use current text
                    self.report({'WARNING'}, "Please save the current text file first")
                    return {'CANCELLED'}
            else:
                # Definition is in another file
                filepath = definition.module_path

            # Use Blender's built-in jump operator
            bpy.ops.text.jump_to_file_at_point(
                filepath=filepath,
                line=definition.line - 1,  # Convert Jedi's 1-based to 0-based indexing
                column=definition.column
            )

            if definition.module_path is None:
                self.report({'INFO'}, f"Jumped to definition at line {definition.line}")
            else:
                filename = Path(filepath).name
                self.report({'INFO'}, f"Jumped to definition in {filename} at line {definition.line}")

        except Exception as e:
            self.report({'WARNING'}, f"Could not jump to definition: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class TEXTIFY_OT_clear_jedi_cache(Operator):
    bl_idname = "textify.clear_jedi_cache"
    bl_label = "Clear Jedi Cache"
    bl_description = "Clear the cached Jedi definitions to free memory"

    def execute(self, context):
        global _jedi_cache
        cache_size = len(_jedi_cache)
        _jedi_cache.clear()
        self.report({'INFO'}, f"Cleared {cache_size} cached definitions")
        return {'FINISHED'}


def menu_func_context(self, context):
    prefs = get_addon_prefs(context)
    space = context.space_data

    if not (
        prefs and
        getattr(prefs, "enable_go_to_definition", False) and
        space and
        space.type == 'TEXT_EDITOR' and
        space.text and
        space.text.current_line_index < len(space.text.lines)
    ):
        return

    text = space.text
    line_text = text.lines[text.current_line_index].body

    # Skip completely empty or whitespace-only lines
    if not line_text.strip():
        return

    layout = self.layout
    layout.operator("textify.goto_definition")
    layout.separator()


def menu_func_edit(self, context):
    prefs = get_addon_prefs(context)
    space = context.space_data

    if not prefs and getattr(prefs, "enable_go_to_definition", False):
        return

    if _jedi_cache:
        self.layout.operator("textify.clear_jedi_cache", icon='TRASH')


def register():
    bpy.utils.register_class(TEXTIFY_OT_goto_definition)
    bpy.utils.register_class(TEXTIFY_OT_clear_jedi_cache)
    bpy.types.TEXT_MT_context_menu.prepend(menu_func_context)
    bpy.types.TEXTIFY_PT_toggle_popover.append(menu_func_edit)


def unregister():
    bpy.types.TEXTIFY_PT_toggle_popover.remove(menu_func_edit)
    bpy.types.TEXT_MT_context_menu.remove(menu_func_context)
    bpy.utils.unregister_class(TEXTIFY_OT_clear_jedi_cache)
    bpy.utils.unregister_class(TEXTIFY_OT_goto_definition)

    # Clear cache on unregister
    global _jedi_cache
    _jedi_cache.clear()
