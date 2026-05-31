# SPDX-FileCopyrightText: See AUTHORS file
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import dot_viewer


class ShowDepsgraphRelationsOperator(bpy.types.Operator):
    bl_idname = "debug.show_depsgraph_relations"
    bl_label = "Show Depsgraph Relations"

    def execute(self, context):
        deg = context.view_layer.depsgraph
        dot_viewer.show(deg.debug_relations_graphviz())
        return {"FINISHED"}


class TOPBAR_MT_CoreDebugTools(bpy.types.Menu):
    bl_label = "Debug"

    def draw(self, context):
        layout = self.layout
        layout.operator("debug.show_depsgraph_relations")


def menu_func(self, context):
    self.layout.menu("TOPBAR_MT_CoreDebugTools")


classes = (ShowDepsgraphRelationsOperator, TOPBAR_MT_CoreDebugTools)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_help.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_help.remove(menu_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
