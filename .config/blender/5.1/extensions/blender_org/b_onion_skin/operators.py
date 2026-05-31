# SPDX-License-Identifier: GPL-3.0-or-later
"""Operators for onion skin addon."""

import bpy
from bpy.types import Operator
from bpy.props import IntProperty

from . import cache


class ONION_OT_add_object(Operator):
    """Add selected objects to onion skin list"""
    bl_idname = "onion_skin.add_object"
    bl_label = "Add Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        existing = {item.object for item in context.scene.onion_skin_objects if item.object}
        added = 0

        for obj in context.selected_objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'ARMATURE'} and obj not in existing:
                context.scene.onion_skin_objects.add().object = obj
                added += 1

        if added > 0:
            cache.clear_cache()

        self.report({'INFO'}, f"Added {added} object(s)")
        return {'FINISHED'}


class ONION_OT_add_from_picker(Operator):
    """Add object from eyedropper selection"""
    bl_idname = "onion_skin.add_from_picker"
    bl_label = "Add Picked Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.onion_skin_settings
        obj = settings.pick_object

        if not obj:
            return {'CANCELLED'}

        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'ARMATURE'}:
            self.report({'WARNING'}, "Only mesh, curve, surface, text, or armature objects supported")
            settings.pick_object = None
            return {'CANCELLED'}

        existing = {item.object for item in context.scene.onion_skin_objects if item.object}

        if obj not in existing:
            context.scene.onion_skin_objects.add().object = obj
            cache.clear_cache()
            self.report({'INFO'}, f"Added: {obj.name}")
        else:
            self.report({'INFO'}, f"Already added: {obj.name}")

        settings.pick_object = None
        return {'FINISHED'}


class ONION_OT_remove_object(Operator):
    """Remove object from onion skin list by index"""
    bl_idname = "onion_skin.remove_object"
    bl_label = "Remove"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        if 0 <= self.index < len(context.scene.onion_skin_objects):
            context.scene.onion_skin_objects.remove(self.index)
            cache.clear_cache()
            cache.clear_ghost_markers()
            context.scene.onion_skin_settings.marker_count = 0
        return {'FINISHED'}


class ONION_OT_remove_selected(Operator):
    """Remove the active object from the list"""
    bl_idname = "onion_skin.remove_selected"
    bl_label = "Remove Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.onion_skin_objects) > 0

    def execute(self, context):
        scene = context.scene
        index = scene.onion_skin_active_index

        if 0 <= index < len(scene.onion_skin_objects):
            scene.onion_skin_objects.remove(index)
            if index >= len(scene.onion_skin_objects) and len(scene.onion_skin_objects) > 0:
                scene.onion_skin_active_index = len(scene.onion_skin_objects) - 1
            cache.clear_cache()
            cache.clear_ghost_markers()
            scene.onion_skin_settings.marker_count = 0
        return {'FINISHED'}


class ONION_OT_clear_all(Operator):
    """Remove all objects from the list"""
    bl_idname = "onion_skin.clear_all"
    bl_label = "Clear All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.onion_skin_objects.clear()
        cache.clear_cache()
        cache.clear_ghost_markers()
        context.scene.onion_skin_settings.marker_count = 0
        return {'FINISHED'}


class ONION_OT_add_marker(Operator):
    """Pin current frame as a persistent ghost overlay"""
    bl_idname = "onion_skin.add_marker"
    bl_label = "Add Ghost"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.onion_skin_objects) > 0

    def execute(self, context):
        from . import drawing

        scene = context.scene
        settings = scene.onion_skin_settings
        frame = scene.frame_current

        objects = drawing.get_mesh_objects(context)
        if not objects:
            self.report({'WARNING'}, "No mesh objects to capture")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        verts, indices, prim_type = drawing.extract_all_meshes_merged(
            objects, depsgraph, settings.use_wireframe
        )

        if not verts or not indices:
            self.report({'WARNING'}, "No mesh data at this frame")
            return {'CANCELLED'}

        cache.add_ghost_marker(frame, verts, indices, prim_type)
        settings.marker_count += 1

        self.report({'INFO'}, f"Ghost added at frame {frame}")
        return {'FINISHED'}


class ONION_OT_remove_markers(Operator):
    """Remove all ghost markers"""
    bl_idname = "onion_skin.remove_markers"
    bl_label = "Remove Ghosts"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cache.clear_ghost_markers()
        context.scene.onion_skin_settings.marker_count = 0

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, "All ghosts removed")
        return {'FINISHED'}


classes = (
    ONION_OT_add_object,
    ONION_OT_add_from_picker,
    ONION_OT_remove_object,
    ONION_OT_remove_selected,
    ONION_OT_clear_all,
    ONION_OT_add_marker,
    ONION_OT_remove_markers,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
