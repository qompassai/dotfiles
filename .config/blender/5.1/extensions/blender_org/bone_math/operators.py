__author__ = "Xury Greer"

# Built-ins
from typing import (
    TYPE_CHECKING,
    Literal,
    cast,
)

# Third Party
import bpy
from bpy.props import (
    EnumProperty,
)
from bpy.types import (
    Armature,
    Context,
    Event,
    KinematicConstraint,
    Object,
    Operator,
    PoseBone,
)
from mathutils import Vector

# First Party
from .pole_angle import (
    get_pole_angle,
)

if TYPE_CHECKING:
    # https://b3d.interplanety.org/en/how-to-properly-specify-the-return-type-of-the-blender-operator-execute-function/
    from bpy.stub_internal.rna_enums import (
        OperatorReturnItems,
    )

    PosePositionItems = Literal["POSE", "REST"]


class OT_BoneMath_CalculatePoleAngle(Operator):
    """Calculate and set the correct pole angle for pose bones that have Inverse Kinematics constraints."""

    bl_idname = "bone_math.calculate_pole_angle"
    bl_label = "Calculate Pole Angle"
    bl_icon = "CON_ROTLIMIT"
    bl_options = {"REGISTER", "UNDO"}

    bones_to_calculate_option: EnumProperty(
        name="Bones to Calculate",
        description="Which bones to calcuate pole angles for",
        items=[
            ("active", "Active", "Only the active pose bone", 0, 0),
            ("selected", "Selected", "All selected pose bones that have IK constraints", 0, 1),
            ("all", "All", "All pose bones in the active armature that have IK constraints", 0, 2),
        ],
        default="active",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if context.mode != "POSE":
            return False

        if not context.active_object:
            return False

        if context.active_object.type != "ARMATURE":
            return False

        return True

    def execute(self, context: Context) -> set["OperatorReturnItems"]:
        bones_to_calculate: list[PoseBone] = []
        armature_object: Object = cast(Object, context.object)
        armature: Armature = cast(Armature, armature_object.data)

        match self.bones_to_calculate_option:
            case "active":
                if context.active_pose_bone:
                    bones_to_calculate.append(context.active_pose_bone)
            case "selected":
                bones_to_calculate = context.selected_pose_bones
            case "all":
                bones_to_calculate = [bone for bone in armature_object.pose.bones]
            case _:
                return {"CANCELLED"}

        if not bones_to_calculate:
            return {"CANCELLED"}

        # Cache the pose position the user had the armature set to.
        original_pose_position: PosePositionItems = armature.pose_position

        for pose_bone in bones_to_calculate:
            # set_pole_angle(context, armature_object, pose_bone)

            # Get the IK constraint.
            ik_constraint: KinematicConstraint | None = None
            for constraint in pose_bone.constraints:
                if constraint.type == "IK":
                    ik_constraint = cast(KinematicConstraint, constraint)
                    break
            else:
                # If there's no IK constraint on this bone, skip it.
                continue

            if not ik_constraint.pole_target:
                # If there's no pole target for this bone, skip it.
                continue
            target_object: Object = cast(Object, ik_constraint.pole_target)

            pole_position: Vector
            if target_object.type == "ARMATURE":
                if not ik_constraint.pole_subtarget:
                    # If the target is an armature, we're expecting a bone sub-target.
                    # if one is not assigned, skip this bone.
                    continue

                # TODO check if the armature or target are not zeroed out.
                # Use the sub-target bone position.
                pole_position = cast(
                    PoseBone, target_object.pose.bones[ik_constraint.pole_subtarget]
                ).matrix.translation
            else:
                # Use the target object position.
                pole_position = target_object.matrix_world.translation

            # The owner of the IK constraint.
            end_bone: PoseBone = pose_bone

            # The start of the IK chain (begin at the end, then walk up the chain).
            start_bone: PoseBone = pose_bone
            chain_length: int = ik_constraint.chain_count
            if chain_length == 0:
                # With a chain length of 0,
                # the chain keeps going until it reaches a bone with no parent.
                while start_bone.parent:
                    start_bone = start_bone.parent
            else:
                # Walk up the bone parent hierarchy to find the start of the chain.
                for _ in range(ik_constraint.chain_count - 1):
                    start_bone = start_bone.parent

            # TODO work with a pole target that belongs to another armature.
            # Switch to rest pose.
            armature.pose_position = "REST"
            # Force an update so we can work with the bones in their resting positions.
            bpy.context.view_layer.update()

            pole_angle: float = get_pole_angle(start_bone, end_bone, pole_position)

            # Switch back to the pose position the user had previously.
            armature.pose_position = original_pose_position

            ik_constraint.pole_angle = pole_angle

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> set["OperatorReturnItems"]:
        if event.alt:
            self.bones_to_calculate_option = "selected"

        return self.execute(context)


classes: list[type] = [
    OT_BoneMath_CalculatePoleAngle,
]


def register() -> None:
    for class_to_register in classes:
        bpy.utils.register_class(class_to_register)


def unregister() -> None:
    for class_to_unregister in classes:
        bpy.utils.unregister_class(class_to_unregister)
