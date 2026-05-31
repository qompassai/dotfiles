# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

class UtilityPanel(bpy.types.Panel):
    """Utility Panel in the Text Editor ui region"""
    bl_label = "Python API Lookup"
    bl_idname = "TEXT_PT_utility"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_context = "text"
    bl_category = "Text"

    def draw(self, context):
        layout = self.layout
        layout.operator("text.python_api_lookup", text="Find Text in Python API")
        layout.operator("screen.userpref_show")

class APILookupOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "text.python_api_lookup"
    bl_label = "API Lookup Operator"
    
    def selected_text(self, context):
        #extract selected string from currently open text
        #from current line till select_end_line
        #from current_character till select_end_character
        #concat
        text = context.edit_text
        if text is None:
            return None
        
        body = ''
        cs = text.current_character
        ce = text.select_end_character
        ls = text.current_line_index
        le = text.select_end_line_index
        #print(ls, le, cs, ce)
        
        #end of selection can be smaller than beginning, so keep correct order
        if ce < cs:
            tmp = ce
            ce = cs
            cs = tmp
            
        if le < ls:
            tmp = le
            le = ls
            ls = tmp
        
        for li in range(ls,le+1):
            l = text.lines[li]
            if ls == le:
                body += l.body[cs:ce]
            elif li == ls:
                body += l.body[cs:]
            elif li == le:
                body += l.body[:ce]             
            else:
                body += l.body
                
        return body

    def execute(self, context):
      
        text = self.selected_text(context)
        if text is None:
            self.report({"ERROR"}, "Please open or create a text in the text editor first")
            return {'CANCELLED'}

        #print(text)
        
        #open browser (2.8+ ?)
        #v = (2, 80, 0) 
        v = bpy.app.version
        version = str(v[0]) + "." + str(v[1])
        base_url = 'https://docs.blender.org/api/'+version+'/'
        url = base_url+'search.html?q='+text+'&check_keywords=yes&area=default'
        bpy.ops.wm.url_open(url=url)
        
        return {'FINISHED'}


def menu_draw(self, context):
    self.layout.separator()
    self.layout.operator("text.api_lookup", text="Find Text in Python API")

def register():
    bpy.utils.register_class(APILookupOperator)
    bpy.utils.register_class(UtilityPanel)
    bpy.types.TEXT_MT_context_menu.append(menu_draw)
    bpy.types.TEXT_MT_edit.append(menu_draw)


def unregister():
    bpy.types.TEXT_MT_edit.remove(menu_draw)
    bpy.types.TEXT_MT_context_menu.remove(menu_draw)
    bpy.utils.unregister_class(UtilityPanel)
    bpy.utils.unregister_class(APILookupOperator)
    
if __name__ == "__main__":
    register()