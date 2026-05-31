# ------------------------------------------------------------------------------------------
#  Copyright (c) Nifs. All rights reserved.
#  Licensed under the GPL-3.0 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------
import math
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import blf
import bmesh
import bpy
import gpu
import numpy as np
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu.types import GPUShaderCreateInfo, GPUStageInterfaceInfo
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

VAILD_TYPE = [
    {
        "type": bpy.types.Constraint,
        "property": ["subtarget", "pole_subtarget"],
        "property_name": ["target", "object"],
    },
    {
        "type": bpy.types.ConstraintTargetBone,
        "property": ["subtarget"],
        "property_name": ["target"],
    },
]

# import cProfile
# import inspect
# import io
# import pstats
# import time
# from functools import wraps
# from typing import Any, Callable


class BoneEyedropperPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    bone_suggestions_color: bpy.props.FloatVectorProperty(
        name="Bone Suggestions Color",
        subtype="COLOR",
        size=4,
        default=(0.0, 1.0, 0.0, 0.7),
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
    )

    line_width: bpy.props.IntProperty(
        name="Line Width",
        default=5,
        min=1,
        max=100,
        soft_min=1,
        soft_max=100,
    )

    text_size: bpy.props.IntProperty(
        name="Text Size",
        default=50,
        min=30,
        max=100,
        soft_min=30,
        soft_max=100,
        subtype="FACTOR",
    )

    text_color: bpy.props.FloatVectorProperty(
        name="Text Color",
        subtype="COLOR",
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
    )

    back_color: bpy.props.FloatVectorProperty(
        name="Background Color",
        subtype="COLOR",
        size=4,
        default=(0.1, 0.1, 0.1, 0.8),
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
    )

    use_rest: bpy.props.BoolProperty(
        name="Use Rest Position",
        default=True,
        description="If enabled, the target armature is automatically rest-posed in edit mode",
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        # How to Use
        row = box.row()
        row.label(text="How to Use:")
        row = box.row()
        row.label(
            text="String/EditBone/PoseBone Property field> Context Menu (Right Click)> Bone Eyedropper"
        )
        row = box.row()
        row.label(
            text="3D View > Context Menu (Right Click)> Bone Eyedropper, (Active Object is Armature)"
        )
        row = layout.row()
        row.prop(self, "bone_suggestions_color")
        row = layout.row()
        row.prop(self, "line_width")
        row = layout.row()
        row.prop(self, "text_size")
        row = layout.row()
        row.prop(self, "text_color")
        row = layout.row()
        row.prop(self, "back_color")
        row = layout.row()
        row.prop(self, "use_rest")


def get_prefereces() -> BoneEyedropperPreferences:
    return bpy.context.preferences.addons[__package__].preferences


class OBJECT_OT_BoneEyedropper(bpy.types.Operator):
    bl_idname = "object.bone_eyedropper"
    bl_label = "Bone Eyedropper"
    bl_description = (
        "Eyedropper a bone from the active object or target and assign it to a property"
    )
    bl_options = {"REGISTER", "UNDO"}

    __handler = None

    copy_name_mode: bpy.props.BoolProperty(
        name="Copy Name Mode",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__min_bone: bpy.types.PoseBone = None
        self.__mousecoord = None
        self.__bonecoord = None
        self.__struct = None
        self.property = None
        self.property_name = None
        self.target = None
        self.hidden = False
        self.bones = []
        self.current_bone_index = 0
        self.depsgraph = None
        self.__evaluated_cache: dict[tuple[Matrix, bpy.types.Mesh]] = {}
        self.__visible_bones_cache = {}
        self.__bone_mesh_cache: dict[bpy.types.PoseBone, bpy.types.Object] = {}
        self.coords_cache_key = None
        self.__coords_cache: dict[bpy.types.PoseBone, list[Vector]] = {}
        self._pose_mode = None

        self.shader_uniform_color = None
        self.shader_bone_mesh = None
        self.flat_bone_data = None

    def __custom_shape_matrix(self, bone: bpy.types.PoseBone) -> Matrix:
        """Get the custom shape matrix of the bone"""
        if bone.custom_shape:
            translation_matrix = Matrix.Translation(bone.custom_shape_translation)
            scale_matrix = Matrix.Diagonal(bone.custom_shape_scale_xyz).to_4x4()
            rotation_matrix = bone.custom_shape_rotation_euler.to_matrix().to_4x4()
            return translation_matrix @ rotation_matrix @ scale_matrix
        return Matrix()

    def __get_evaluated(
        self, bone: bpy.types.PoseBone
    ) -> tuple[Matrix, bpy.types.Mesh]:
        """Get the evaluated of the custom shape of the bone"""

        def create_bbone_mesh(bbone: bpy.types.PoseBone):
            bm = bmesh.new()

            for i in range(bbone.bone.bbone_segments):
                cube = bmesh.ops.create_cube(bm, size=0.2)

                if bbone.bone.bbone_segments > 1:
                    # Get the current and next segment matrices
                    mat_current = bbone.bbone_segment_matrix(i, rest=False)
                    mat_next = bbone.bbone_segment_matrix(i + 1, rest=False)
                    # Lerp between the two matrices to reproduce BBone (not correct)
                    blended_matrix = mat_current.lerp(mat_next, 0.5)
                    matrix_final = bbone.matrix @ blended_matrix
                else:
                    matrix_final = bbone.matrix
                    bmesh.ops.translate(
                        bm, verts=cube["verts"], vec=Vector((0, 0.1, 0))
                    )
                bmesh.ops.scale(bm, verts=cube["verts"], vec=Vector((1, 5, 1)))
                # Display size Scale
                x = bbone.bone.bbone_x * 10
                z = bbone.bone.bbone_z * 10
                l = bbone.length / bbone.bone.bbone_segments
                bmesh.ops.scale(bm, verts=cube["verts"], vec=Vector((x, l, z)))
                bmesh.ops.transform(bm, verts=cube["verts"], matrix=matrix_final)

            mesh_data = bpy.data.meshes.new("BBone_Mesh")
            bmesh.ops.transform(bm, matrix=Matrix.Diagonal(bone.scale).to_4x4())
            bm.to_mesh(mesh_data)
            bm.free()
            mesh_obj = bpy.data.objects.new("BBone", mesh_data)

            return mesh_obj

        if self.target.data.pose_position == "POSE":
            if bone.custom_shape:
                mesh_obj = bone.custom_shape
                mesh_obj = mesh_obj.evaluated_get(self.depsgraph)
                if bone.custom_shape_transform:
                    override_mat = bone.custom_shape_transform.matrix
                    b_mat = override_mat
                else:
                    b_mat = bone.matrix

                # Apply bone scale
                mat = (
                    self.target.matrix_world @ b_mat @ self.__custom_shape_matrix(bone)
                )
                if bone.use_custom_shape_bone_size:
                    mat = mat @ Matrix.Scale(bone.bone.length, 4)

            elif bone.id_data.data.display_type == "BBONE":
                mesh_obj = create_bbone_mesh(bone)
                mat = bone.id_data.matrix_world
                self.__bone_mesh_cache[bone] = mesh_obj
            else:
                mesh_obj = get_asset()
                loc, rot, _ = bone.matrix.decompose()
                bone_tr_matrix = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
                mat = (
                    self.target.matrix_world
                    @ bone_tr_matrix
                    @ Matrix.Scale(bone.length, 4)
                )
                self.__bone_mesh_cache[bone] = mesh_obj
            if mesh_obj.type != "MESH":
                mesh = mesh_obj.to_mesh()
            else:
                mesh = mesh_obj.data
        else:
            mesh_obj = get_asset()
            edit_bone = self.target.data.edit_bones.get(bone.name)
            mat = (
                self.target.matrix_world
                @ edit_bone.matrix
                @ Matrix.Scale(edit_bone.length, 4)
            )
            self.__bone_mesh_cache[bone] = mesh_obj
            if mesh_obj.type != "MESH":
                mesh = mesh_obj.to_mesh()
            else:
                mesh = mesh_obj.data
        return mat, mesh

    def __get_evaluated_cached(
        self, bone: bpy.types.PoseBone
    ) -> tuple[Matrix, bpy.types.Mesh]:
        """Get the evaluated of the custom shape of the bone with caching"""
        if bone in self.__evaluated_cache:
            return self.__evaluated_cache[bone]
        result = self.__get_evaluated(bone)
        self.__evaluated_cache[bone] = result
        return result

    def __handle_add(self, context):
        if OBJECT_OT_BoneEyedropper.__handler is None:
            OBJECT_OT_BoneEyedropper.__handler = bpy.types.SpaceView3D.draw_handler_add(
                self.__draw, (context,), "WINDOW", "POST_PIXEL"
            )

    def __handle_remove(self, context):
        if OBJECT_OT_BoneEyedropper.__handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                OBJECT_OT_BoneEyedropper.__handler, "WINDOW"
            )
            OBJECT_OT_BoneEyedropper.__handler = None

    def __end(self, context, area):
        self.__handle_remove(context)

        if hasattr(self, "original_pose_position"):
            self.target.data.pose_position = self.original_pose_position


        context.window.cursor_set("DEFAULT")
        context.workspace.status_text_set(None)
        area.tag_redraw()
        for mesh_obj in self.__bone_mesh_cache.values():
            try:
                bpy.data.meshes.remove(mesh_obj.data)
            except Exception:
                pass
        self.__evaluated_cache.clear()
        self.__visible_bones_cache.clear()
        self.__bone_mesh_cache.clear()
        self.__coords_cache.clear()
        # p = pstats.Stats(self.pr)
        # p.sort_stats(pstats.SortKey.TIME, pstats.SortKey.CUMULATIVE)
        # p.print_stats()
        # self.pr.disable()

        self.shader_uniform_color = None
        self.shader_bone_mesh = None

    def __draw(self, context):
        if self.__min_bone and self.__mousecoord and self.__bonecoord:
            # pref
            pref = get_prefereces()
            gpu.state.blend_set("ALPHA")

            mouse_offset = 50

            main_width_max = pref.text_size * 6
            main_width_offset = 10
            main_height_offset = 10

            # Calculate position
            x = self.__mousecoord.x + mouse_offset
            y = self.__mousecoord.y + mouse_offset

            # Set text size and get dimensions
            font_id = 0
            blf.size(font_id, pref.text_size)
            main_width, main_height = blf.dimensions(font_id, self.__min_bone.name)

            main_width = max(main_width, pref.text_size + main_width_max)
            main_height = max(main_height, pref.text_size + main_height_offset)
            # Set background color and draw rounded rectangle
            self.draw_rounded_rectangle(
                pref,
                x,
                -main_width_offset,
                y,
                -main_height_offset,
                main_width,
                main_width_offset,
                main_height,
                -main_height_offset // 2,
            )

            # Draw Bone Name
            blf.position(font_id, x, y, 0)
            blf.color(
                font_id,
                pref.text_color[0],
                pref.text_color[1],
                pref.text_color[2],
                pref.text_color[3],
            )
            blf.draw(font_id, self.__min_bone.name)

            # Draw Next and Prev Bone names

            blf.size(font_id, pref.text_size // 2)
            nx_ix = (
                self.current_bone_index + 1
                if self.current_bone_index + 1 < len(self.bones)
                else None
            )
            pr_ix = (
                self.current_bone_index - 1
                if self.current_bone_index - 1 >= 0
                else None
            )

            # Fixed offset for Next and Prev labels
            fixed_offset = main_height + 5
            for offset_multiplier, label, index in [
                (-1, "Next", nx_ix),
                (1, "Prev", pr_ix),
            ]:
                offset = offset_multiplier * fixed_offset
                blf.position(font_id, x, y + offset, 0)
                text = (
                    f"{label}: {self.bones[index][0].name if index is not None else ''}"
                )
                text_width, text_height = blf.dimensions(font_id, text)
                text_width = main_width // 2
                text_height = main_height // 5
                self.draw_rounded_rectangle(
                    pref,
                    x,
                    -main_width_offset,
                    y + offset,
                    -main_height_offset,
                    text_width,
                    main_width_offset,
                    text_height,
                    -main_height_offset // 2,
                )
                blf.draw(font_id, text)

            blf.size(font_id, pref.text_size // 3)
            blf.position(font_id, x, y - main_height * 2 - 5, 0)
            text = "Ctrl+Wheel Up/Down: Change closest bone | Shift: Get hidden bones"
            blf.draw(font_id, text)

            # Draw dashed line
            self.__draw_dashed_line()

            # Draw bone mesh
            self.__draw_bone_mesh(context)

    def draw_rounded_rectangle(
        self, pref, x, x_offset, y, y_offset, width, width_offset, height, height_offset
    ):
        shader = self.shader_uniform_color
        radius = 5
        vertices = self.__rounded_rect_vertices(
            x + x_offset,
            y + y_offset,
            width + width_offset,
            height + height_offset,
            radius,
        )

        gpu.state.blend_set("ALPHA")
        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", pref.back_color)
        batch.draw(shader)
        gpu.state.blend_set("NONE")

    def __draw_dashed_line(self, dash_length=10):
        start = self.__mousecoord
        end = self.__bonecoord
        shader = self.shader_uniform_color
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))

        total_length = (end - start).length
        num_dashes = int(total_length / dash_length)
        direction = (end - start).normalized()

        vertices = []
        for i in range(num_dashes):
            if i % 2 == 0:
                segment_start = start + direction * (i * dash_length)
                segment_end = start + direction * ((i + 1) * dash_length)
                vertices.extend([segment_start, segment_end])

        batch = batch_for_shader(shader, "LINES", {"pos": vertices})
        batch.draw(shader)

    def __create_bone_mesh_batch(self, shader, data):
        me = data
        me.calc_loop_triangles()
        # vertices
        vs = np.zeros(
            (len(me.vertices) * 3,),
            dtype=np.float32,
        )
        me.vertices.foreach_get("co", vs)
        vs.shape = (
            -1,
            3,
        )
        # edges
        es = np.zeros(
            (len(me.edges) * 2,),
            dtype=np.int32,
        )
        me.edges.foreach_get("vertices", es)
        es.shape = (
            -1,
            2,
        )
        # faces
        fs = np.zeros(
            (len(me.loop_triangles) * 3,),
            dtype=np.int32,
        )
        me.loop_triangles.foreach_get("vertices", fs)
        fs.shape = (
            -1,
            3,
        )
        # colors
        cs = np.full(
            (len(me.vertices), 4),
            get_prefereces().bone_suggestions_color,
            dtype=np.float32,
        )

        # if object has no faces, draw edges
        if len(fs) == 0:
            batch = batch_for_shader(
                shader,
                "LINES",
                {
                    "position": vs,
                    "color": cs,
                },
                indices=es,
            )
            gpu.state.line_width_set(get_prefereces().line_width)
        else:
            batch = batch_for_shader(
                shader,
                "TRIS",
                {
                    "position": vs,
                    "color": cs,
                },
                indices=fs,
            )
        return batch

    def __draw_bone_mesh(self, context):
        matrix, data = self.__get_evaluated_cached(self.__min_bone)
        shader = self.shader_bone_mesh
        batch = self.__create_bone_mesh_batch(shader, data)
        gpu.state.blend_set("ADDITIVE")
        shader.bind()
        shader.uniform_float("model", matrix)
        shader.uniform_float("projection", context.region_data.perspective_matrix)
        batch.draw(shader)

    def __rounded_rect_vertices(self, x, y, width, height, radius):
        def corner_vertices(cx, cy, start_angle):
            return [
                (
                    cx
                    + radius * math.cos(start_angle + (i / segments) * (math.pi / 2)),
                    cy
                    + radius * math.sin(start_angle + (i / segments) * (math.pi / 2)),
                )
                for i in range(segments + 1)
            ]

        vertices = []
        segments = 4

        # Bottom-left corner
        vertices.extend(corner_vertices(x + radius, y + radius, math.pi))
        # Bottom-right corner
        vertices.extend(corner_vertices(x + width - radius, y + radius, -math.pi / 2))
        # Top-right corner
        vertices.extend(corner_vertices(x + width - radius, y + height - radius, 0))
        # Top-left corner
        vertices.extend(corner_vertices(x + radius, y + height - radius, math.pi / 2))

        return vertices

    def __get_closest_vertex_to_cursor(
        self, mesh, mat, region, space, coord, bone: bpy.types.PoseBone
    ):
        current_key = (
            Vector((region.width, region.height)),
            space.region_3d.perspective_matrix,
            self.hidden,
        )
        if (
            self.coords_cache_key == current_key
            and bone.name in self.__coords_cache
            and self.__coords_cache[bone.name] is not None
        ):
            bcoords_np = self.__coords_cache[bone.name]
            if bcoords_np.shape[0] == 0:
                return None
            distances = np.linalg.norm(
                bcoords_np - np.array([coord.x, coord.y]), axis=1
            )
            min_index = np.argmin(distances)
            return Vector(bcoords_np[min_index])

        num_verts = len(mesh.vertices)
        if num_verts == 0:
            self.__coords_cache[bone.name] = np.empty((0, 2))
            return None

        local_verts_N3 = np.empty((num_verts, 3), dtype=np.float32)
        mesh.vertices.foreach_get("co", local_verts_N3.ravel())

        bcoords_np = self.__project_vertices_to_screen_batch(
            local_verts_N3, mat, region, space.region_3d
        )

        self.__coords_cache[bone.name] = bcoords_np

        if bcoords_np.shape[0] > 0:
            distances = np.linalg.norm(
                bcoords_np - np.array([coord.x, coord.y]), axis=1
            )
            min_index = np.argmin(distances)
            return Vector(bcoords_np[min_index])

        return None

    def __project_vertices_to_screen_batch(
        self,
        local_verts_N3: np.ndarray,
        world_matrix_b: Matrix,
        region: bpy.types.Region,
        rv3d: bpy.types.SpaceView3D,
    ) -> np.ndarray:
        num_verts = local_verts_N3.shape[0]

        world_matrix_np = np.array(world_matrix_b)
        proj_matrix_np = np.array(rv3d.perspective_matrix)

        local_verts_N4 = np.hstack(
            (local_verts_N3, np.ones((num_verts, 1), dtype=np.float32))
        )

        # MVPMatrix
        #    Local -> World -> View -> Proj
        #    (N, 4) @ (4, 4)^T @ (4, 4)^T @ (4, 4)^T
        #    = (N, 4) @ (Proj @ View @ World)^T
        mvp_matrix = proj_matrix_np @ world_matrix_np

        # transform to clip space
        #    (N, 4) @ (4, 4)^T
        clip_verts_N4 = local_verts_N4 @ mvp_matrix.T

        # perspective divide
        #    ignore w <= 0 (behind camera)
        valid_indices = clip_verts_N4[:, 3] > 1e-5
        if not np.any(valid_indices):
            return np.empty((0, 2))  # no valid vertices

        valid_clip_verts = clip_verts_N4[valid_indices]

        # NDC (N_valid, 3)
        #    div by w 
        ndc_verts_N3 = valid_clip_verts[:, 0:3] / valid_clip_verts[:, 3, np.newaxis]

        # (N_valid, 2)
        #    NDC (-1 to 1) -> Screen (0 to width/height)
        screen_verts_N2 = (ndc_verts_N3[:, 0:2] + 1.0) / 2.0
        screen_verts_N2[:, 0] = screen_verts_N2[:, 0] * region.width
        screen_verts_N2[:, 1] = screen_verts_N2[:, 1] * region.height

        return screen_verts_N2

    def __get_closest_bones(self, context, event, region, space):
        coord = Vector((event.mouse_x - region.x, event.mouse_y - region.y))

        visible_pose_bones = self.__get_visible_pose_bones()

        visible_flat_data = [
            self.flat_bone_data[b.name]
            for b in visible_pose_bones
            if b.name in self.flat_bone_data
        ]


        bone_distances = []
        current_pose_position = self.target.data.pose_position

        for bone_data in visible_flat_data:
            bcoord = None

            if bone_data.has_custom_shape or bone_data.is_bbone:

                if bone_data.mat_mesh is None:
                    bone_data.mat_mesh = self.__get_evaluated_cached(
                        bone_data.pose_bone
                    )

                mat, mesh = bone_data.mat_mesh
                bcoord = self.__get_closest_vertex_to_cursor(
                    mesh, mat, region, space, coord, bone_data.pose_bone
                )

            else:
                if current_pose_position == "POSE":
                    bone_world_center = bone_data.pose_center
                else:
                    bone_world_center = bone_data.rest_center

                bcoord = location_3d_to_region_2d(
                    region, space.region_3d, bone_world_center
                )

            if bcoord:
                dist = (bcoord - coord).length
                bone_distances.append((bone_data.pose_bone, dist, bcoord))

        bone_distances.sort(key=lambda x: x[1])

        self.coords_cache_key = (
            Vector((region.width, region.height)),
            space.region_3d.perspective_matrix.copy(),
            self.hidden,
        )

        return bone_distances

    def __get_visible_pose_bones(self) -> List[bpy.types.PoseBone]:
        """Get visible pose bones with caching"""
        consider_hidden_bones = self.hidden
        cache_key = (self.target, consider_hidden_bones)
        if cache_key in self.__visible_bones_cache:
            return self.__visible_bones_cache[cache_key]

        arm: bpy.types.Armature = self.target.data
        visible_bones = {}
        if arm.pose_position == "REST":
            visible_bones = {
                b.name: b for b in arm.edit_bones if not b.hide or consider_hidden_bones
            }
        elif hasattr(arm, "collections_all"):
            # Get bones from visible Bone Collections
            visible_bones = {
                b.name: b
                for c in arm.collections_all
                if c.is_visible or consider_hidden_bones
                for b in c.bones
                if not b.hide or consider_hidden_bones
            }
            # Bones that don't belong to any collection
            all_bones = set(arm.bones)
            collection_bones = {b for c in arm.collections_all for b in c.bones}
            non_collection_bones = all_bones - collection_bones
            visible_bones.update(
                {
                    b.name: b
                    for b in non_collection_bones
                    if not b.hide or consider_hidden_bones
                }
            )
        else:
            # In pose position, use bones
            visible_bones = {
                b.name: b for b in arm.bones if not b.hide or consider_hidden_bones
            }

        # Convert to pose bones
        pose_bones = self.target.pose.bones
        result = [
            pose_bones.get(b_name)
            for b_name in visible_bones
            if pose_bones.get(b_name) is not None
        ]

        self.__visible_bones_cache[cache_key] = result
        return result

    def modal(self, context, event):
        # Update status text
        # try:
        context.workspace.status_text_set(
            f"Ctl+Wheel: Change closest bone | Shift: Get hidden bones | LMB: Set bone | RMB/Esc: Cancel"
        )

        context.window.cursor_set("EYEDROPPER")
        region, area, space = get_region_under_cursor(context, event)
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.__end(context, area)
            return {"CANCELLED"}

        pref = get_prefereces()
        self.hidden = event.shift
        if region is None:
            # Cursor is not in a 3D view or Outliner
            return {"PASS_THROUGH"}
        if area.type == "OUTLINER":
            # TODO:How to get active bone from outliner context?
            return {"PASS_THROUGH"}
        elif area.type == "VIEW_3D":
            if event.type == "MOUSEMOVE":
                self.current_bone_index = 0
            # Get min bone from the list
            self.bones = self.__get_closest_bones(context, event, region, space)
            if event.type == "WHEELUPMOUSE" and event.ctrl:
                # limit the index to the length of the list
                self.current_bone_index = min(
                    self.current_bone_index + 1, len(self.bones) - 1
                )
                area.tag_redraw()
            elif event.type == "WHEELDOWNMOUSE" and event.ctrl:
                # limit the index to 0
                self.current_bone_index = max(self.current_bone_index - 1, 0)
                area.tag_redraw()
            try:
                self.__min_bone = self.bones[self.current_bone_index][0]
                self.__bonecoord = self.bones[self.current_bone_index][2]
            except IndexError:
                self.__min_bone = None
                self.__bonecoord = None
            self.__mousecoord = Vector(
                (event.mouse_x - region.x, event.mouse_y - region.y)
            )
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                # Set
                if self.__min_bone:
                    if self.copy_name_mode:
                        # Copy bone name to clipboard
                        bpy.context.window_manager.clipboard = self.__min_bone.name
                        self.report(
                            {"INFO"}, f"Copied {self.__min_bone.name} to clipboard"
                        )
                        self.__end(context, area)
                        return {"FINISHED"}
                    try:
                        # is RNAattribute?
                        rna_prop = self.__struct.bl_rna.properties.get(
                            self.property_name
                        )

                        if rna_prop:
                            prop_type = rna_prop.type

                            if prop_type == "STRING":
                                print(
                                    f"RNA-STRING: Setting {self.property_name} to {self.__min_bone.name}"
                                )
                                setattr(
                                    self.__struct,
                                    self.property_name,
                                    self.__min_bone.name,
                                )

                            elif prop_type == "POINTER":
                                pointer_type = rna_prop.fixed_type

                                if pointer_type == bpy.types.PoseBone.bl_rna:
                                    print(
                                        f"RNA-POINTER (PoseBone): Setting {self.property_name}"
                                    )
                                    setattr(
                                        self.__struct,
                                        self.property_name,
                                        self.__min_bone,
                                    )

                                elif pointer_type == bpy.types.EditBone.bl_rna:
                                    print(
                                        f"RNA-POINTER (EditBone): Setting {self.property_name}"
                                    )
                                    edit_bone = self.target.data.edit_bones.get(
                                        self.__min_bone.name
                                    )
                                    if edit_bone:
                                        setattr(
                                            self.__struct, self.property_name, edit_bone
                                        )
                                    else:
                                        print(
                                            f"Error: EditBone '{self.__min_bone.name}' not found."
                                        )

                                else:
                                    print(
                                        f"Unsupported RNA-POINTER type: {pointer_type}"
                                    )
                            else:
                                print(f"Unsupported RNA property type: {prop_type}")

                        else:
                            if self.property_name not in self.__struct:
                                print(
                                    f"Custom property '{self.property_name}' does not exist. Assuming string assignment."
                                )
                                self.__struct[self.property_name] = self.__min_bone.name
                            else:
                                current_value = self.__struct.get(self.property_name)

                                try:
                                    if isinstance(current_value, str):
                                        print(f"CUSTOM (str): Setting {self.property_name}")
                                        self.__struct[self.property_name] = (
                                            self.__min_bone.name
                                        )

                                    elif isinstance(current_value, bpy.types.PoseBone):
                                        print(
                                            f"CUSTOM (PoseBone): Setting {self.property_name}"
                                        )
                                        self.__struct[self.property_name] = self.__min_bone

                                    elif isinstance(current_value, bpy.types.EditBone):
                                        print(
                                            f"CUSTOM (EditBone): Setting {self.property_name}"
                                        )
                                        edit_bone = self.target.data.edit_bones.get(
                                            self.__min_bone.name
                                        )
                                        if edit_bone:
                                            self.__struct[self.property_name] = edit_bone
                                        else:
                                            print(
                                                f"Error: EditBone '{self.__min_bone.name}' not found."
                                            )

                                    elif current_value is None:
                                        print(
                                            f"CUSTOM (None): Defaulting to set string (name) for {self.property_name}"
                                        )
                                        self.__struct[self.property_name] = (
                                            self.__min_bone.name
                                        )

                                    else:
                                        print(
                                            f"Unsupported custom property type: {type(current_value)}"
                                        )

                                except TypeError as e:
                                    print(
                                        f"Error: This object ({self.__struct.rna_type.name}) does not support custom properties: {e}"
                                    )
                        self.report({"INFO"}, f"Set property to {self.__min_bone.name}")
                        self.__end(context, area)
                        return {"FINISHED"}
                    except Exception as e:
                        self.report({"ERROR"}, f"Error setting property: {e}")
                        print(self.__struct, self.property_name, self.__min_bone.name)
                        print(type(getattr(self.__struct, self.property_name)))
                        self.__end(context, area)
                        return {"CANCELLED"}
                self.__end(context, area)
                return {"FINISHED"}
        area.tag_redraw()
        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        # self.pr = cProfile.Profile()
        # self.pr.enable()

        self.shader_uniform_color = gpu.shader.from_builtin("UNIFORM_COLOR")
        self.shader_bone_mesh = self.__create_bone_mesh_shader()

        if self.copy_name_mode == False:
            self.__struct = context.button_pointer
            self.property = context.button_prop
            self.property_name = self.property.identifier

            # Get struct
            dict = next(
                (
                    item
                    for item in VAILD_TYPE
                    if item["type"] == type(self.__struct)
                    or issubclass(type(self.__struct), item["type"])
                ),
                None,
            )
            if dict:
                # if self.property_name in dict["property"]:
                for prop in dict["property_name"]:
                    if hasattr(self.__struct, prop):
                        self.target = getattr(self.__struct, prop)
                        # if type(self.target) != bpy.types.Object:
                        #     # TODO: temporary
                        #     self.target = context.active_object
                        break
                else:
                    self.report(
                        {"ERROR"},
                        f"None of the properties {dict['property_name']} found in struct",
                    )
                    return {"CANCELLED"}

            if self.target is None:
                self.target = context.active_object
            if self.target.type != "ARMATURE":
                self.report({"ERROR"}, f"Active object is not an armature")
                return {"CANCELLED"}

        else:
            # When called directly, mode to copy only the name of the bone for the active object
            self.copy_name_mode = True
            self.target = context.active_object
            if type(self.target.data) != bpy.types.Armature:
                self.report({"ERROR"}, f"Active object is not an armature")
                return {"CANCELLED"}
            self.report({"INFO"}, "Copy bone name mode")
        self.depsgraph = context.evaluated_depsgraph_get()
        self.__evaluated_cache.clear()
        self.__visible_bones_cache.clear()
        self.__bone_mesh_cache.clear()
        self.__coords_cache.clear()
        self.__handle_remove(context)
        self.__handle_add(context)

        pref = get_prefereces()
        if pref.use_rest:
            self.original_pose_position = self.target.data.pose_position

            if context.mode == "EDIT_ARMATURE":
                self.target.data.pose_position = "REST"
            else:
                self.target.data.pose_position = "POSE"

        context.view_layer.update()


        self.flat_bone_data: dict[str, BoneCacheData] = {}
        matrix_world = self.target.matrix_world
        all_pose_bones = list(self.target.pose.bones)
        N = len(all_pose_bones)

        if N == 0:
            return {"RUNNING_MODAL"}
        
        all_edit_bones_map = self.target.data.edit_bones
        edit_bones_ordered = [all_edit_bones_map.get(pb.name) for pb in all_pose_bones]

        pose_heads_N3 = np.array([pb.head for pb in all_pose_bones])
        pose_tails_N3 = np.array([pb.tail for pb in all_pose_bones])
        edit_heads_N3 = np.array([eb.head if eb else (0, 0, 0) for eb in edit_bones_ordered])
        edit_tails_N3 = np.array([eb.tail if eb else (0, 0, 0) for eb in edit_bones_ordered])

        ones_N1 = np.ones((N, 1), dtype=np.float32)
        pose_heads_N4 = np.hstack((pose_heads_N3, ones_N1))
        pose_tails_N4 = np.hstack((pose_tails_N3, ones_N1))
        edit_heads_N4 = np.hstack((edit_heads_N3, ones_N1))
        edit_tails_N4 = np.hstack((edit_tails_N3, ones_N1))

        mw_np_T = np.array(matrix_world).T

        world_pose_heads_N3 = (pose_heads_N4 @ mw_np_T)[:, :3]
        world_pose_tails_N3 = (pose_tails_N4 @ mw_np_T)[:, :3]
        world_edit_heads_N3 = (edit_heads_N4 @ mw_np_T)[:, :3]
        world_edit_tails_N3 = (edit_tails_N4 @ mw_np_T)[:, :3]

        world_pose_centers_N3 = (world_pose_heads_N3 + world_pose_tails_N3) * 0.5
        world_edit_centers_N3 = (world_edit_heads_N3 + world_edit_tails_N3) * 0.5

        eb_exists_mask = np.array([eb is not None for eb in edit_bones_ordered])
        has_custom_shape_list = np.array([bool(pb.custom_shape) for pb in all_pose_bones])
        display_types_list = np.array(
            [pb.id_data.data.display_type for pb in all_pose_bones]
        )
        segments_list = np.array([pb.bone.bbone_segments for pb in all_pose_bones])
        is_bbone_list = (display_types_list == "BBONE") & (segments_list > 1)

        for i, pb in enumerate(all_pose_bones):
            eb = edit_bones_ordered[i]
            eb_exists = eb_exists_mask[i]

            rest_head_vec = world_edit_heads_N3[i] if eb_exists else world_pose_heads_N3[i]
            rest_tail_vec = world_edit_tails_N3[i] if eb_exists else world_pose_tails_N3[i]
            rest_center_vec = (
                world_edit_centers_N3[i] if eb_exists else world_pose_centers_N3[i]
            )

            flat_data = BoneCacheData(
                name=pb.name,
                pose_bone=pb,
                edit_bone=eb,
                pose_head=Vector(world_pose_heads_N3[i]),
                pose_tail=Vector(world_pose_tails_N3[i]),
                pose_center=Vector(world_pose_centers_N3[i]),
                rest_head=Vector(rest_head_vec),
                rest_tail=Vector(rest_tail_vec),
                rest_center=Vector(rest_center_vec),

                has_custom_shape=has_custom_shape_list[i],
                is_bbone=is_bbone_list[i],
            )
            self.flat_bone_data[pb.name] = flat_data

        context.window_manager.modal_handler_add(self)
        print(
            f"struct: {self.__struct}, property: {self.property_name}, target: {self.target.name}"
        )
        return {"RUNNING_MODAL"}

    def __create_bone_mesh_shader(self):
        interface = GPUStageInterfaceInfo("BoneMesh")
        interface.smooth("VEC3", "out_pos")
        interface.smooth("VEC4", "out_color")

        shader_info = GPUShaderCreateInfo()
        shader_info.vertex_in(0, "VEC3", "position")
        shader_info.vertex_in(1, "VEC4", "color")
        shader_info.push_constant("MAT4", "model")
        shader_info.push_constant("MAT4", "projection")
        shader_info.vertex_out(interface)
        shader_info.fragment_out(0, "VEC4", "FragColor")
        shader_info.vertex_source(
            "void main()"
            "{"
            "    vec3 pos = vec3(model * vec4(position, 1.0));"
            "    gl_Position = projection * vec4(pos, 1.0);"
            "    out_color = color;"
            "}"
        )
        # In 4.4, using blender_srgb_to_framebuffer_space causes a compile error ??
        shader_info.fragment_source(
            "vec4 srgb_to_framebuffer_space(vec4 in_color)"
            "{"
            "       vec3 c = max(in_color.rgb, vec3(0.0));"
            "       vec3 c1 = c * (1.0 / 12.92);"
            "       vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));"
            "       in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));"
            "  return in_color;"
            "}"
            "void main()"
            "{"
            "    FragColor = srgb_to_framebuffer_space(out_color);"
            "}"
        )
        shader = gpu.shader.create_from_info(shader_info)
        del interface
        del shader_info
        return shader


@dataclass
class BoneCacheData:
    name: str
    pose_bone: bpy.types.PoseBone
    edit_bone: Optional[bpy.types.EditBone]

    pose_head: Vector
    pose_tail: Vector
    pose_center: Vector
    rest_head: Vector
    rest_tail: Vector
    rest_center: Vector

    has_custom_shape: bool
    is_bbone: bool

    mat_mesh: Optional[tuple[Matrix, bpy.types.Mesh]] = field(default=None)


def load_object(blend_file_path, object_name):
    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        if object_name in data_from.objects:
            data_to.objects.append(object_name)
            return data_to.objects[0]
        else:
            print(f"Object '{object_name}' not found in '{blend_file_path}'")


def get_asset(type=None):
    asset_name = "BoneEyeDropper_Bone_Default"
    try:
        # Fix: use a unique name or another way to get the object
        return bpy.data.objects[asset_name]
    except KeyError:
        pass
    addon_directory = os.path.dirname(__file__)
    blend_file_path = os.path.join(addon_directory, "assets", "Bone_Asset.blend")
    return bpy.data.objects[load_object(blend_file_path, asset_name)]


def get_region_under_cursor(
    context, event
) -> tuple[bpy.types.Region, bpy.types.Area, bpy.types.SpaceView3D]:
    for area in context.screen.areas:
        if area.type == "VIEW_3D" or "OUTLINER":
            for region in area.regions:
                if region.type == "WINDOW":
                    # Check if cursor is in the region
                    if (
                        region.x <= event.mouse_x <= region.x + region.width
                        and region.y <= event.mouse_y <= region.y + region.height
                    ):
                        space = area.spaces.active
                        return region, area, space
    return None, None, None


def draw_menu(self: bpy.types.Panel, context: bpy.types.Context):
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"

    add_operator = False
    copy_name_mode = False
    if context and hasattr(context, "button_pointer") and context.button_pointer:
        try:
            attr = getattr(context.button_pointer, context.property[1])
        except Exception:
            attr = ""

        if isinstance(attr, (str, bpy.types.EditBone)) or (
            hasattr(context.button_prop, "fixed_type")
            and isinstance(context.button_prop.fixed_type, bpy.types.PoseBone)
        ):
            add_operator = True
            copy_name_mode = False
    elif isinstance(
        self,
        (
            bpy.types.VIEW3D_MT_object_context_menu,
            bpy.types.VIEW3D_MT_armature_context_menu,
            bpy.types.VIEW3D_MT_pose_context_menu,
        ),
    ):
        if context.active_object and context.active_object.type == "ARMATURE":
            add_operator = True
            copy_name_mode = True
    if add_operator:
        layout.separator()
        op = layout.operator(
            OBJECT_OT_BoneEyedropper.bl_idname,
            text="Bone Eyedropper",
            icon="EYEDROPPER",
        )
        op.copy_name_mode = copy_name_mode


classes = [
    OBJECT_OT_BoneEyedropper,
    BoneEyedropperPreferences,
]


def register_component():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.UI_MT_button_context_menu.append(draw_menu)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_menu)
    bpy.types.VIEW3D_MT_pose_context_menu.append(draw_menu)
    bpy.types.VIEW3D_MT_armature_context_menu.append(draw_menu)


def unregister_component():
    bpy.types.UI_MT_button_context_menu.remove(draw_menu)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_menu)
    bpy.types.VIEW3D_MT_pose_context_menu.remove(draw_menu)
    bpy.types.VIEW3D_MT_armature_context_menu.remove(draw_menu)
    for cls in classes:
        bpy.utils.unregister_class(cls)