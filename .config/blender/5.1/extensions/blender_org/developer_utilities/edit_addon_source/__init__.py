# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import StringProperty


def draw(**kwargs):
    from .. import DeveloperUtilitiesPreferences, Pid
    
    global olddraw
    
    olddraw(**kwargs)

    #print(kwargs)
    layout = kwargs['layout']
    mod = kwargs['mod']

    #just append the new operator here
    split = layout.split(factor=0.15)
    col_a = split.column()
    split = split.split(factor=0.5)
    col_b = split.column()
    col_c = split.column()
    col_a.alignment = 'RIGHT'

    col_a.label(text="Development")
    col_b.operator("wm.addon_edit_sources", text="Edit Addon Sources", icon='TEXT').module = mod.__name__

    addon_prefs = bpy.context.preferences.addons[DeveloperUtilitiesPreferences.bl_idname].preferences

    try:
        import pdoc
    except ImportError as e:
        col_c.operator("pdoc.install",text="Install missing pdoc dependency")
        return 
    
    if Pid.pid == -1:
        op = col_c.operator("pdoc.generate", text="Generate Documentation", icon="FILE_TEXT")
        op.module_name = mod.__name__
        op.server = addon_prefs.use_server
        op.port = addon_prefs.server_port
        op.target = addon_prefs.target_dir
    else:
        op = col_c.operator("pdoc.kill", text="Stop running server")
        op.pid = Pid.pid


class WM_OT_addon_edit(Operator):
    "Edit the addon source files"
    bl_idname = "wm.addon_edit_sources"
    bl_label = "Edit Addon Sources"

    module : StringProperty(
            name="Module",
            description="Module name of the addon to edit",
            )

    def load_sources(self, context, filepaths):
        import subprocess, os
        from .. import DeveloperUtilitiesPreferences

        user_preferences = context.preferences
        addon_prefs = user_preferences.addons[DeveloperUtilitiesPreferences.bl_idname].preferences
        text_editor = user_preferences.filepaths.text_editor
        use_external = addon_prefs.use_external

        if not text_editor or not use_external:
            for path in filepaths:
                bpy.data.texts.load(path)
                self.report({'INFO'}, "Loaded source file: %r" % path)
             
            return {'FINISHED'}

        else:
            text_editor = os.path.abspath(text_editor)
            cmd = [text_editor] + filepaths
    
            try:
                subprocess.Popen(cmd)
            except:
                import traceback
                traceback.print_exc()
                self.report({'ERROR'},
                            "Text editor not found, "
                            "please specify in Preferences > Filepaths > Applications > Text Editor")
                return {'CANCELLED'}

            return {'FINISHED'}
    
    @staticmethod
    def path_from_addon(module):
        import os
        import addon_utils

        for mod in addon_utils.modules():
            if mod.__name__ == module:
                filepath = mod.__file__
                if os.path.exists(filepath):
                    if os.path.splitext(os.path.basename(filepath))[0] == "__init__":
                        return os.path.dirname(filepath), True
                    else:
                        return filepath, False
        return None, False

    def execute(self, context):
        import os

        path, isdir = WM_OT_addon_edit.path_from_addon(self.module)
        if path is None:
            self.report({'WARNING'}, "Addon path %r could not be found" % path)
            return {'CANCELLED'}

        filepaths = []
        # walk through dir recursively to find all py files and load them
        if isdir:
             for root, dirs, files in os.walk(path):
                 for file in files:
                     if file.endswith(".py"):
                        filepath = os.path.join(root, file);
                        filepaths.append(filepath)
        else:
             filepaths = [path]

        return self.load_sources(context, filepaths)


def register():
    bpy.utils.register_class(WM_OT_addon_edit)
    import bl_pkg.bl_extension_ui as ui
    
    #re-assign method
    global olddraw 
    olddraw = ui.addon_draw_item_expanded
    ui.addon_draw_item_expanded = draw
   
    
def unregister():
    global olddraw
    
    #restore method
    import bl_pkg.bl_extension_ui 
    bl_pkg.bl_extension_ui.addon_draw_item_expanded = olddraw

    bpy.utils.unregister_class(WM_OT_addon_edit)
