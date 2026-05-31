"""
Adapted from: https://blender.stackexchange.com/a/19755
by Jaroslav Jerryno Novotny
"""

__author__ = "Xury Greer"

# Third Party
from math import atan2

from bpy.types import (
    PoseBone,
)
from mathutils import (
    Vector,
)


def signed_angle(
    vector_a: Vector,
    vector_b: Vector,
    normal: Vector,
) -> float:
    """Get the signed angle between two vectors.

    :param vector_a: The first vector.
    :param vector_b: The second vector.
    :param normal: A reference normal vector, the sign will be determined by this orientation.
        This vector does not need to be normalized.
    :return: The signed angle between the two vectors around the given reference normal.
    """

    # Ensure all arguments have a magnitude greater than 0.
    if any(vector.magnitude == 0.0 for vector in (vector_a, vector_b, normal)):
        raise ValueError(
            "Can't calculate signed angle, one or more of the given inputs has zero magnitude:\n"
            f"vector_a: '{vector_a}'\n"
            f"vector_b: '{vector_b}'\n"
            f"normal:   '{normal}'\n"
        )

    # Normalize the vectors to get pure direction with a magnitude of 1.0.
    direction_a: Vector = vector_a.normalized()
    direction_b: Vector = vector_b.normalized()

    # Since the vectors are normalized, the dot product will give us
    # the cosine of the unsigned angle between the vectors.
    a_dot_b: float = direction_a.dot(direction_b)

    # The unsigned angle from 0.0 to pi can be calculated with arccosine: `acos(a_dot_b)`.
    # However, we need more information to get the signed angle from -pi to pi.

    # direction_c is the cross product of direction_b and direction_a, so it is perpendicular to both.
    # Its dot product with the reference normal tells us the orientation of the rotation from a to b relative to the normal's direction.
    direction_c: Vector = direction_b.cross(direction_a)
    normal_dot_c: float = normal.dot(direction_c)

    # `atan2(sin, cos)` gives us the signed angle from -pi to pi.
    # normal_dot_c represents the sine component.
    # a_dot_b represents the cosine component.
    signed_angle_radians: float = atan2(normal_dot_c, a_dot_b)

    return signed_angle_radians


def get_pole_angle(
    start_bone: PoseBone,
    end_bone: PoseBone,
    pole_location: Vector,
) -> float:
    """Calculate the pole angle for bones in an IK chain.
    The resulting angle will align the IK chain so that the bones don't move from their rest positions.

    Pole angle is a signed angle between the start_bone's X axis and
    the projected pole_axis onto start_bone's XZ plane.
    The direction of projection is IK_axis.

    :param start_bone: The first bone in the IK chain.
    :param end_bone: The final bone in the IK chain.
    :param pole_location: The location of the pole target.
    :return: The signed angle value in radians that is required to make the IK chain aim
        at the pole target so that it matches the resting pose.
    """

    # Axis aimed from the base of the chain to the end of the chain.
    start_to_end: Vector = end_bone.tail - start_bone.head

    # Axis aimed from the base of the chain, to the pole target.
    start_to_pole: Vector = pole_location - start_bone.head

    pole_normal: Vector = start_to_end.cross(start_to_pole)

    projected_pole_axis: Vector = pole_normal.cross(start_bone.y_axis)

    try:
        pole_angle: float = signed_angle(
            start_bone.x_axis,
            projected_pole_axis,
            start_bone.y_axis,
        )

        return pole_angle
    except ValueError as e:
        print(e)
        return 0.0
