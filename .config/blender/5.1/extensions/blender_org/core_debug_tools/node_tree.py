# SPDX-FileCopyrightText: See AUTHORS file
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import dot_viewer


class ShowLazyFunctionGraphOperator(bpy.types.Operator):
    bl_idname = "debug.show_lazy_function_graph"
    bl_label = "Show Lazy-Function Graph"

    @classmethod
    def poll(cls, context):
        if context.area.type != "NODE_EDITOR":
            return False
        if context.space_data.edit_tree is None:
            return False
        return True

    def execute(self, context):
        tree = context.space_data.edit_tree
        dot_str = tree.debug_lazy_function_graph()

        if dot_str:
            dot_viewer.show(dot_str)
        return {"FINISHED"}


class ShowZoneBodyLazyFunctionGraphOperator(bpy.types.Operator):
    bl_idname = "debug.show_zone_body_lazy_function_graph"
    bl_label = "Show Zone Body Lazy-Function Graph"

    @classmethod
    def poll(cls, context):
        if context.area.type != "NODE_EDITOR":
            return False
        if context.space_data.edit_tree is None:
            return False
        if context.active_node is None:
            return False
        return True

    def execute(self, context):
        node = context.active_node
        dot_str = node.debug_zone_body_lazy_function_graph()
        if dot_str:
            dot_viewer.show(dot_str)
        return {"FINISHED"}


class ShowZoneLazyFunctionGraphOperator(bpy.types.Operator):
    bl_idname = "debug.show_zone_lazy_function_graph"
    bl_label = "Show Zone Lazy-Function Graph"

    @classmethod
    def poll(cls, context):
        if context.area.type != "NODE_EDITOR":
            return False
        if context.space_data.edit_tree is None:
            return False
        if context.active_node is None:
            return False
        return True

    def execute(self, context):
        node = context.active_node
        dot_str = node.debug_zone_lazy_function_graph()
        if dot_str:
            dot_viewer.show(dot_str)
        return {"FINISHED"}


class NODE_MT_CoreDebugTools(bpy.types.Menu):
    bl_label = "Debug"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODE_MT_CoreDebugToolsLazyFunction")


class NODE_MT_CoreDebugToolsLazyFunction(bpy.types.Menu):
    bl_label = "Lazy-Function"

    def draw(self, context):
        layout = self.layout
        layout.operator("debug.show_lazy_function_graph", text="Group")
        layout.operator("debug.show_zone_lazy_function_graph", text="Zone")
        layout.operator("debug.show_zone_body_lazy_function_graph", text="Zone Body")


def menu_func(self, context):
    self.layout.menu("NODE_MT_CoreDebugTools")


classes = (
    ShowLazyFunctionGraphOperator,
    ShowZoneBodyLazyFunctionGraphOperator,
    ShowZoneLazyFunctionGraphOperator,
    NODE_MT_CoreDebugTools,
    NODE_MT_CoreDebugToolsLazyFunction,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.NODE_MT_node.append(menu_func)


def unregister():
    bpy.types.NODE_MT_node.remove(menu_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
