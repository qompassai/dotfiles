# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import time
import os
from typing import Iterable, List, Optional, Tuple

bl_info = {
    "name": "Simple Audio Visualizer",
    "author": "Polyfjord",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "Graph Editor > Sidebar > Simple Audio Visualizer",
    "description": "Creates a simple audio visualizer",
    "category": "Animation",
}

_ADDON_VERSION_STR = "1.2.0"


# --------------------------------------------------------------------------
# Blender 5.0+ compatibility helpers (Action Slots & Channelbags)
# --------------------------------------------------------------------------
def _version_at_least(major: int, minor: int = 0, patch: int = 0) -> bool:
    return bpy.app.version >= (major, minor, patch)


def _ensure_anim_data_action(obj: bpy.types.ID) -> Tuple[bpy.types.AnimData, bpy.types.Action]:
    """Ensure obj.animation_data and obj.animation_data.action exist and return them."""
    anim_data = obj.animation_data
    if anim_data is None:
        anim_data = obj.animation_data_create()

    action = anim_data.action
    if action is None:
        action = bpy.data.actions.new(name=f"{obj.name}Action")
        anim_data.action = action

    # Blender 4.4+ introduced Action Slots; in 5.0 the slot/channelbag is required.
    if hasattr(anim_data, "action_slot"):
        if anim_data.action_slot is None:
            # Try to create a matching slot for this object.
            # Signature differs across versions; accept both positional and keyword styles.
            try:
                slot = action.slots.new('OBJECT', obj.name)
            except TypeError:
                slot = action.slots.new(id_type='OBJECT', name=obj.name)
            anim_data.action_slot = slot

    return anim_data, action


def _get_fcurves_collection(obj: bpy.types.Object) -> Iterable[bpy.types.FCurve]:
    """
    Return an iterable collection of FCurves for the object's current action.
    Blender 5.0 removed Action.fcurves; FCurves are now accessed via the action slot's channelbag.
    """
    anim_data, action = _ensure_anim_data_action(obj)

    if _version_at_least(5, 0, 0):
        if not hasattr(anim_data, "action_slot") or anim_data.action_slot is None:
            raise RuntimeError("No action slot available for this object (required in Blender 5.0+).")

        from bpy_extras import anim_utils

        # Some corner cases can have a slot but no channelbag yet; ensure it exists if possible.
        channelbag = None
        if hasattr(anim_utils, "action_ensure_channelbag_for_slot"):
            channelbag = anim_utils.action_ensure_channelbag_for_slot(action, anim_data.action_slot)
        else:
            channelbag = anim_utils.action_get_channelbag_for_slot(action, anim_data.action_slot)

        if channelbag is None:
            raise RuntimeError("Could not get channelbag for action slot (Blender 5.0+).")

        return channelbag.fcurves

    # Blender <= 4.5: legacy direct access still exists
    return action.fcurves


def _fcurve_find(fcurves: Iterable[bpy.types.FCurve], data_path: str, index: int) -> Optional[bpy.types.FCurve]:
    """
    Find a curve by data_path and array index for both legacy Action.fcurves and channelbag.fcurves.
    """
    # Collections often have .find(), but it's not guaranteed for all iterables.
    if hasattr(fcurves, "find"):
        try:
            return fcurves.find(data_path, index=index)
        except TypeError:
            try:
                return fcurves.find(data_path, index)
            except Exception:
                pass

    for fc in fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def _fcurve_remove(fcurves: Iterable[bpy.types.FCurve], fc: bpy.types.FCurve) -> None:
    """Remove FCurve from its collection (legacy or channelbag)."""
    if hasattr(fcurves, "remove"):
        fcurves.remove(fc)  # type: ignore[attr-defined]
        return
    # Fallback: no-op (should not happen in Blender's RNA collections)
    raise RuntimeError("This Blender build does not support removing fcurves via the collection.")


def _graph_editor_override(context: bpy.types.Context) -> dict:
    """
    Build a safe temp_override dict for Graph Editor operators.
    Works when invoked from the Graph Editor panel, and tries to locate a Graph Editor otherwise.
    """
    window = context.window
    screen = context.screen

    area = None
    region = None

    if context.area and context.area.type == 'GRAPH_EDITOR':
        area = context.area
    else:
        if window and screen:
            for a in screen.areas:
                if a.type == 'GRAPH_EDITOR':
                    area = a
                    break

    if area:
        for r in area.regions:
            if r.type == 'WINDOW':
                region = r
                break

    if not (window and screen and area and region):
        raise RuntimeError("Graph Editor context not available. Open a Graph Editor and try again.")

    return {"window": window, "screen": screen, "area": area, "region": region}


# --------------------------------------------------------------------------
# Core baking logic
# --------------------------------------------------------------------------
def bake_sound_to_channels(
    obj: bpy.types.Object,
    context: bpy.types.Context,
    path: str,
    lo: float,
    hi: float,
    intensity_multiplier: float,
    anim_loc: bool,
    anim_rot: bool,
    anim_scale: bool,
    anim_x: bool,
    anim_y: bool,
    anim_z: bool,
    additive_mode: bool = False,
) -> None:
    """
    Bakes sound data to specified transform channels of a given object.
    Blender 5.0 compatibility: uses action slots/channelbags instead of Action.fcurves.
    """
    # Ensure anim data/action/slot exist.
    _ensure_anim_data_action(obj)

    props_to_animate: List[str] = []
    if anim_loc:
        props_to_animate.append("location")
    if anim_rot:
        props_to_animate.append("rotation_euler")
    if anim_scale:
        props_to_animate.append("scale")

    axes_to_animate: List[int] = []
    if anim_x:
        axes_to_animate.append(0)
    if anim_y:
        axes_to_animate.append(1)
    if anim_z:
        axes_to_animate.append(2)

    if not props_to_animate or not axes_to_animate:
        return  # Nothing to do

    # Ensure we're baking from the start of the scene.
    scene = context.scene
    if scene is not None:
        scene.frame_set(scene.frame_start)

    # Get fcurves for current action/slot.
    fcurves = _get_fcurves_collection(obj)

    # Remove existing curves (clean bake) unless additive.
    if not additive_mode:
        for fc in list(fcurves):
            if fc.data_path in props_to_animate and fc.array_index in axes_to_animate:
                _fcurve_remove(fcurves, fc)

    # Ensure the fcurves exist by inserting a keyframe on each channel.
    # (This is also the most compatible way to get the correct action slot/channelbag set up.)
    fcs_to_bake: List[bpy.types.FCurve] = []
    current_frame = scene.frame_current if scene else 1

    for prop in props_to_animate:
        for axis in axes_to_animate:
            fc = _fcurve_find(fcurves, prop, axis)
            if fc is None:
                obj.keyframe_insert(data_path=prop, index=axis, frame=current_frame, group=prop)
                # Re-fetch collection (keyframe_insert can create data structures lazily).
                fcurves = _get_fcurves_collection(obj)
                fc = _fcurve_find(fcurves, prop, axis)

            if fc is not None:
                fcs_to_bake.append(fc)

    if not fcs_to_bake:
        print(f"[Simple Audio Visualizer] Warning: Could not create any F-Curves for {obj.name}")
        return

    # Graph Editor operators require correct UI context.
    override = _graph_editor_override(context)

    # Make sure obj is active (Graph ops typically target active animation context).
    view_layer = context.view_layer
    original_active = view_layer.objects.active if view_layer else None
    if view_layer:
        view_layer.objects.active = obj

    try:
        with context.temp_override(**override):
            # Deselect all curves in the current collection.
            for fc in fcurves:
                try:
                    fc.select = False
                except Exception:
                    pass

            # Select only the curves we want to bake.
            for fc in fcs_to_bake:
                fc.select = True

            # Bake to selected curves.
            bpy.ops.graph.sound_to_samples(filepath=path, low=lo, high=hi, use_additive=additive_mode)
            bpy.ops.graph.samples_to_keys()

        # Apply intensity multiplier.
        if intensity_multiplier != 1.0:
            for fc in fcs_to_bake:
                for kf in fc.keyframe_points:
                    kf.co.y *= intensity_multiplier
                    kf.handle_left.y *= intensity_multiplier
                    kf.handle_right.y *= intensity_multiplier
                fc.update()

        # Deselect after baking.
        for fc in fcs_to_bake:
            try:
                fc.select = False
            except Exception:
                pass

    finally:
        if view_layer:
            view_layer.objects.active = original_active


# --------------------------------------------------------------------------
# Properties / Operators / UI
# --------------------------------------------------------------------------
class SimpleAudioVisualizerProperties(bpy.types.PropertyGroup):
    columns: bpy.props.IntProperty(
        name="Number of cubes",
        default=20,
        min=1,
        description="Number of created objects. Higher values will increase calculation time.",
    )
    path: bpy.props.StringProperty(
        name="Audio File",
        subtype="FILE_PATH",
        description="Set the path to the audio file.",
    )
    mirror_mode: bpy.props.BoolProperty(
        name="Mirror Mode",
        default=False,
        description="Offsets the origins of the cubes to create a mirror effect.",
    )
    intensity: bpy.props.FloatProperty(
        name="Audio Visualizer Multiplier",
        default=1.0,
        min=0.0,
        soft_max=20.0,
        description="Multiplier for the animation's strength",
    )
    animate_location: bpy.props.BoolProperty(
        name="Location",
        default=False,
        description="Animate Location",
    )
    animate_rotation: bpy.props.BoolProperty(
        name="Rotation",
        default=False,
        description="Animate Rotation",
    )
    animate_scale: bpy.props.BoolProperty(
        name="Scale",
        default=True,
        description="Animate Scale",
    )
    animate_axis_x: bpy.props.BoolProperty(
        name="X",
        default=False,
        description="Animate X Axis",
    )
    animate_axis_y: bpy.props.BoolProperty(
        name="Y",
        default=False,
        description="Animate Y Axis",
    )
    animate_axis_z: bpy.props.BoolProperty(
        name="Z",
        default=True,
        description="Animate Z Axis",
    )
    additive_mode: bpy.props.BoolProperty(
        name="Additive",
        default=False,
        description=(
            "Add animation from the previous frame to the next, instead of replacing it. "
            "Recommended for use with the Rotation channel."
        ),
    )

    # Dummy properties for UI tooltips
    info_generate: bpy.props.BoolProperty(
        name=(
            "Generate audio visualizer objects in your scene that will be animated based on the selected Audio File. "
            "Uses a logarithmic frequency distribution."
        ),
        description="",
        default=False,
    )
    info_animate: bpy.props.BoolProperty(
        name=(
            "Apply animation data to selected objects in your scene by specifying which transform channels and axes "
            "will receive the data. The frequency bands are distributed between the number of selected objects and "
            "sorted in alphabetical order."
        ),
        description="",
        default=False,
    )


class SimpleAudioVisualizerOperator(bpy.types.Operator):
    bl_idname = "object.simple_audio_visualizer"
    bl_label = "Create Objects"
    bl_description = "Creates new cube objects and animates them to the audio"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sav_props = context.scene.sav_props

        if not sav_props.path:
            self.report({"ERROR"}, "Please specify an audio file path first.")
            return {"CANCELLED"}

        path = os.path.abspath(bpy.path.abspath(sav_props.path))
        if not os.path.exists(path):
            self.report({"ERROR"}, f"Audio file not found: {path}")
            return {"CANCELLED"}

        start_time = time.time()

        columns = sav_props.columns
        intensity = sav_props.intensity
        spectrum_start = 10.0   # Hz
        spectrum_end = 21000.0  # Hz
        mirror_mode = sav_props.mirror_mode

        maxheight = 6.0
        l = 1.0
        h = spectrum_start
        base = (spectrum_end / spectrum_start) ** (1.0 / columns)

        print(f"[Simple Audio Visualizer] STARTED (Cubes_Spectrum={columns})")

        # Jump to start frame without operators (more context-safe).
        context.scene.frame_set(context.scene.frame_start)

        def create_and_bake_cube(x, y, zmax, lo, hi, intensity_multiplier):
            bpy.ops.mesh.primitive_cube_add(location=(x, y, 0))
            obj = bpy.context.active_object

            if mirror_mode:
                # Cube origin is centered by default (mirror scaling around Z=0).
                pass
            else:
                # Set origin to cube base using cursor.
                bpy.context.scene.cursor.location = obj.location
                bpy.context.scene.cursor.location.z -= 1
                bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
                obj.location.z += 1

            obj.scale.x = 0.4
            obj.scale.y = 0.4
            obj.scale.z = zmax
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            bake_sound_to_channels(
                obj,
                context,
                path,
                lo,
                hi,
                intensity_multiplier,
                anim_loc=False,
                anim_rot=False,
                anim_scale=True,
                anim_x=False,
                anim_y=False,
                anim_z=True,
                additive_mode=False,
            )

        for i in range(columns):
            l = h
            h = round(spectrum_start * (base ** (i + 1)), 2)
            print(f"     c: {i}   l: {l} Hz    h: {h} Hz")

            create_and_bake_cube(0, i, maxheight, l, h, intensity)

            done_percent = (i + 1) / columns * 100
            elapsed_minutes = (time.time() - start_time) / 60
            print(f"[Simple Audio Visualizer] {done_percent:.1f}%   done in {elapsed_minutes:.2f} minutes")

        print(f"[Simple Audio Visualizer] CREATED {columns} OBJECTS")

        bpy.context.scene.cursor.location = (0, 0, 0)

        # Clean selection state.
        if bpy.context.active_object:
            bpy.context.active_object.select_set(False)
            bpy.context.view_layer.objects.active = None

        return {"FINISHED"}


class VisualizeSelectedObjectsOperator(bpy.types.Operator):
    bl_idname = "object.visualize_selected_objects"
    bl_label = "Visualize Selected Objects"
    bl_description = "Animate the selected objects based on the audio."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        sav_props = context.scene.sav_props
        selected_objects = context.selected_objects

        if not sav_props.path:
            self.report({"ERROR"}, "Please specify an audio file path first.")
            return {"CANCELLED"}

        path = os.path.abspath(bpy.path.abspath(sav_props.path))
        if not os.path.exists(path):
            self.report({"ERROR"}, f"Audio file not found: {path}")
            return {"CANCELLED"}

        has_channel = sav_props.animate_location or sav_props.animate_rotation or sav_props.animate_scale
        has_axis = sav_props.animate_axis_x or sav_props.animate_axis_y or sav_props.animate_axis_z

        if not has_channel or not has_axis:
            self.report({"ERROR"}, "Please select at least one transform (Loc/Rot/Scale) and one axis (X/Y/Z).")
            return {"CANCELLED"}

        start_time = time.time()

        columns = len(selected_objects)
        intensity = sav_props.intensity
        spectrum_start = 10.0
        spectrum_end = 21000.0

        l = 1.0
        h = spectrum_start
        base = (spectrum_end / spectrum_start) ** (1.0 / columns)

        print(f"[Simple Audio Visualizer] STARTED (Visualizing {columns} selected objects)")
        context.scene.frame_set(context.scene.frame_start)

        sorted_objects = sorted(selected_objects, key=lambda o: o.name)
        original_active = context.view_layer.objects.active

        for i, obj in enumerate(sorted_objects):
            context.view_layer.objects.active = obj

            l = h
            h = round(spectrum_start * (base ** (i + 1)), 2)
            print(f"     Animating: {obj.name}   l: {l} Hz    h: {h} Hz")

            bake_sound_to_channels(
                obj,
                context,
                path,
                l,
                h,
                intensity,
                sav_props.animate_location,
                sav_props.animate_rotation,
                sav_props.animate_scale,
                sav_props.animate_axis_x,
                sav_props.animate_axis_y,
                sav_props.animate_axis_z,
                sav_props.additive_mode,
            )

            done_percent = (i + 1) / columns * 100
            elapsed_minutes = (time.time() - start_time) / 60
            print(f"[Simple Audio Visualizer] {done_percent:.1f}%   done in {elapsed_minutes:.2f} minutes")

        context.view_layer.objects.active = original_active
        print(f"[Simple Audio Visualizer] FINISHED Animating {columns} objects")

        return {"FINISHED"}


class SimpleAudioVisualizerPanel(bpy.types.Panel):
    bl_label = "Simple Audio Visualizer"
    bl_idname = "GRAPH_EDITOR_PT_simple_audio_visualizer"
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
    bl_category = "Simple Audio Visualizer"

    def draw(self, context):
        layout = self.layout
        sav_props = context.scene.sav_props

        layout.prop(sav_props, "path")
        layout.prop(sav_props, "intensity")
        layout.separator()

        box_create = layout.box()
        row = box_create.row()
        row.label(text="Generate New Objects")
        row.alignment = "RIGHT"
        row.prop(sav_props, "info_generate", text="", icon="QUESTION", emboss=False)
        box_create.prop(sav_props, "columns")
        box_create.prop(sav_props, "mirror_mode")
        box_create.operator("object.simple_audio_visualizer", text="Create Visualizer")

        box_visualize = layout.box()
        row = box_visualize.row()
        row.label(text="Animate Selected Objects")
        row.alignment = "RIGHT"
        row.prop(sav_props, "info_animate", text="", icon="QUESTION", emboss=False)

        sub_box = box_visualize.box()
        col = sub_box.column(align=True)

        row = col.row(align=True)
        row.prop(sav_props, "animate_location", toggle=True)
        row.prop(sav_props, "animate_rotation", toggle=True)
        row.prop(sav_props, "animate_scale", toggle=True)

        row = col.row(align=True)
        row.prop(sav_props, "animate_axis_x", toggle=True)
        row.prop(sav_props, "animate_axis_y", toggle=True)
        row.prop(sav_props, "animate_axis_z", toggle=True)

        box_visualize.prop(sav_props, "additive_mode")

        row = box_visualize.row()
        row.enabled = bool(context.selected_objects)
        row.operator("object.visualize_selected_objects", text="Visualize Selected Objects")


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------
_CLASSES = (
    SimpleAudioVisualizerProperties,
    SimpleAudioVisualizerOperator,
    VisualizeSelectedObjectsOperator,
    SimpleAudioVisualizerPanel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.sav_props = bpy.props.PointerProperty(type=SimpleAudioVisualizerProperties)


def unregister():
    if hasattr(bpy.types.Scene, "sav_props"):
        del bpy.types.Scene.sav_props

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
