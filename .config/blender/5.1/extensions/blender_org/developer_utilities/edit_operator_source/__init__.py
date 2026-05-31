# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import sys
import inspect
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup
        )
from bpy.props import (
        EnumProperty,
        StringProperty,
        IntProperty
        )

def list_submodules(package):
    
    import pkgutil, importlib
    
    """List all submodules of a given package without importing them."""
    submodules = []
    path = package.__path__
    prefix = package.__name__ + '.'

    for _, name, is_pkg in pkgutil.iter_modules(path, prefix):
        submodules.append(importlib.import_module(name))
        if is_pkg:
            submodules.extend(list_submodules(importlib.import_module(name)))
    return submodules

def parent(i):
    import ast
    while hasattr(i, "parent"):
        if i.parent is None:
            break
        if isinstance(i, ast.ClassDef):
            break
        if isinstance(i, ast.FunctionDef) and not i.parent is None and not isinstance(i.parent, ast.ClassDef):
            break

        i = i.parent

    if hasattr(i, "name"):
        return i.name
    else:
        return None

def check_for_calls(a, opname, filepath):
    #opname is "text.edit_operator"
    #can be found as is as first arg
    #or as call with
    import ast

    calls = []
    w = list(ast.walk(a))
    for i in w:
        for child in ast.iter_child_nodes(i):
            child.parent = i
            #print(node)

    for i in w:
        if isinstance(i, ast.Call):
            if isinstance(i.func, ast.Attribute):
                #print("ATTR CALL",ast.unparse(i), ast.unparse(i.func.value), i.func.attr)
                cls = ast.unparse(i.func.value)
                nm = i.func.attr
                #print(cls, nm, opname)
                if opname == f"{cls}.{nm}".replace("bpy.ops.",""):
                    p = parent(i)
                    if p is not None:
                        print("FOUND", p, filepath, i.lineno, i.col_offset)
                        call = [opname, p, filepath, i.lineno, i.col_offset]
                        calls.append(call)
                
                if i.func.attr == "operator":
                    if len(i.args) > 0:
                        if hasattr(i.args[0], "value"):
                            val = i.args[0].value
                            if isinstance(i.args[0].value, ast.Name):
                                val = ast.unparse(i.args[0].value)  
                            #print(val, opname, type(val), type(opname), opname == val)  
                            if opname == val:
                                p = parent(i)
                                if p is not None:
                                    print("FOUND", p, filepath, i.lineno, i.col_offset)
                                    call = [opname, p , filepath, i.lineno, i.col_offset]
                                    calls.append(call)
                        
            #if isinstance(i.func, ast.Name):
            #    print("NAME CALL",i.func.id)
    return calls

def find_calls(module, method_name):
    import ast
    calls = []
    #submodules = walk_module(module,exclude=["sys"],visited=None)
    try: 
        tree = ast.parse(inspect.getsource(module))
        filepath = inspect.getfile(module)
        calls.extend(check_for_calls(tree, method_name, filepath))
    except Exception as e:
        print(e)

    try: 
        submodules = list_submodules(module)
        for submod in submodules:
            tree = ast.parse(inspect.getsource(submod))
            filepath = inspect.getfile(submod)
            calls.extend(check_for_calls(tree, method_name, filepath))
    except Exception as e:
        print(e)

    return calls

def walk_module(module, exclude=[], visited=None):
    if visited is None:
        visited = set()
        
    if module in visited:
        return []
    
    visited.add(module)
    
    submodules = []
    for name, m in inspect.getmembers(module):
        if inspect.ismodule(m):
            found = False
            for x in exclude:
                if m.__name__.startswith(x):
                    found = True
                    break
            if found:
                continue
            submodules.append(m)
            submodules.extend(walk_module(m, exclude=exclude, visited=visited))
    return submodules


def getclazz(opname):
    opid = opname.split(".")
    opmod = getattr(bpy.ops, opid[0])
    op = getattr(opmod, opid[1])
    id = op.get_rna_type().bl_rna.identifier
    try:
        clazz = getattr(bpy.types, id)
        return clazz
    except AttributeError:
        return None


def getmodule(opname):
    addon = True
    clazz = getclazz(opname)

    if clazz is None:
        return  "", -1, False

    modn = clazz.__module__

    try:
        line = inspect.getsourcelines(clazz)[1]
    except IOError:
        line = -1
    except TypeError:
        line = -1

    if modn == 'bpy.types':
        mod = 'C operator'
        addon = False
    elif modn != '__main__':
        mod = sys.modules[modn].__file__
    else:
        addon = False
        mod = modn

    return mod, line, addon


def get_ops():
    import inspect
    op_strings = []
    tot = 0
    for op_module_name in dir(bpy.ops):
        op_module = getattr(bpy.ops, op_module_name)
        for op_submodule_name in dir(op_module):
            op = getattr(op_module, op_submodule_name)
            text = repr(op)
            if text.split("\n")[-1].startswith("bpy.ops."):
                text = text.replace("bpy.ops.", "").split("(")[0]
                op_strings.append(text)
                tot += 1

    # add own operator name too, since its not loaded yet when this is called
    
    # seems our own module's operators are not being loaded / added into  bpy.ops, who knows why...
    # ...so add manually... 
    op_strings.append("text.edit_operator")
    op_strings.append("text.python_api_lookup")
    op_strings.append("wm.addon_edit_sources")
    op_strings.append("pdoc.generate")
    op_strings.append("pdoc.kill")
    op_strings.append("pdoc.install")
    #   
    l = sorted(op_strings)
    del op_strings

    return [(y, y, "", x) for x, y in enumerate(l)]

class OperatorEntry(PropertyGroup):

    label : StringProperty(
            name="Label",
            description="",
            default=""
            )

    path : StringProperty(
            name="Path",
            description="",
            default=""
            )

    line : IntProperty(
            name="Line",
            description="",
            default=-1
            )
    offset : IntProperty(
            name="Offset",
            description="",
            default=-1
            )

class TEXT_OT_EditOperator(Operator):
    bl_idname = "text.edit_operator"
    bl_label = "Edit Operator"
    bl_description = "Opens the source file of operators chosen from Menu"
    bl_property = "op"

    items = get_ops()

    op : EnumProperty(
            name="Op",
            description="",
            items=items
            )

    path : StringProperty(
            name="Path",
            description="",
            default=""
            )

    line : IntProperty(
            name="Line",
            description="",
            default=-1
            )
    
    column : IntProperty(
            name="Line",
            description="",
            default=-1
            )

    def show_text(self, context, path, line, column):
        found = False

        for t in bpy.data.texts:
            if t.filepath == path:
                #switch to the wanted text first
                context.space_data.text = t
                ctx = context.copy()
                ctx['edit_text'] = t
                with context.temp_override(**ctx):
                    bpy.ops.text.jump(line=line)
                    #bpy.ops.text.jump_to_file_at_point(filepath='', line=line, column=column)
                found = True
                break

        if (found is False):
            self.report({'INFO'},
                        "Opened file: " + path)
            bpy.ops.text.open(filepath=path)
            #bpy.ops.text.jump_to_file_at_point(filepath='', line=line, column=column)
            bpy.ops.text.jump(line=line)

    def show_calls(self, context):
        import bl_ui, bl_ext, bl_pkg
        import os
        
        exclude = []

        #avoid builtin classes, they dont have sources or files at hand
        #exclude.append("bpy")
        #exclude.append("bpy.ops")
        #exclude.append("bpy.types")
        exclude.append("sys")
        #exclude.append("bl_ui")

        calls = []
        calls.extend(find_calls(bl_ui, self.op))
        d = dir(bl_ext)
        for x in d:
            if not x.startswith("__"):
                mod = getattr(bl_ext, x)
                calls.extend(find_calls(mod, self.op))

        #print("CALLS", calls)
        for c in calls:
            cl = context.scene.calls.add()
            cl.name = c[0]
            cl.label = f"{c[1]} : {os.path.basename(c[2])}:{c[3]}"
            cl.path = c[2]
            cl.line = c[3]
            cl.column = c[4]
            #print("CALL", cl)

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'PASS_THROUGH'}

    def execute(self, context):
        import os

        if self.path != "" and self.line != -1:
            #invocation of one of the "found" locations
            self.show_text(context, self.path, self.line, self.column)
            return {'FINISHED'}
        else:
            context.scene.calls.clear()
            path, line, addon = getmodule(self.op)

            if addon:
                #self.show_text(context, path, line, -1)

                #add convenient "source" button, to toggle back from calls to source
                c = context.scene.calls.add()
                c.name = self.op
                c.label = f"Source : {os.path.basename(path)}:{line}"
                c.path = path
                c.line = line
                c.column = -1

                self.show_calls(context)
                context.area.tag_redraw()

                return {'FINISHED'}
            else:

                self.report({'WARNING'},
                            "Found no source file for " + self.op)

                self.show_calls(context)
                context.area.tag_redraw()

                return {'FINISHED'}


class TEXT_PT_EditOperatorPanel(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Edit Operator"
    bl_category = "Text"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        op = layout.operator("text.edit_operator")
        op.path = ""
        op.line = -1

        if len(context.scene.calls) > 0:
            box = layout.box()
            box.label(text="Calls of: " + context.scene.calls[0].name)
            box.operator_context = 'EXEC_DEFAULT'
            for c in context.scene.calls:
                op = box.operator("text.edit_operator", text=c.label)
                op.path = c.path
                op.line = c.line
                op.op = c.name


def register():
    bpy.utils.register_class(OperatorEntry)
    bpy.types.Scene.calls = bpy.props.CollectionProperty(name="Calls",
                                                         type=OperatorEntry)
    bpy.utils.register_class(TEXT_OT_EditOperator)
    bpy.utils.register_class(TEXT_PT_EditOperatorPanel)


def unregister():
    bpy.utils.unregister_class(TEXT_PT_EditOperatorPanel)
    bpy.utils.unregister_class(TEXT_OT_EditOperator)
    del bpy.types.Scene.calls
    bpy.utils.unregister_class(OperatorEntry)


if __name__ == "__main__":
    register()
    bpy.ops.text.edit_operator()
