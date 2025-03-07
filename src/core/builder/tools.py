from __future__ import annotations

from core.definitions.geometry import Axis
from ..detection import Detection


def get_lines(detections: list[Detection], distance_threshold: float) -> list[list[Detection]]:
    """
    Groups detections into horizontal lines based on a vertical distance threshold.

    Parameters
    ----------
    detections : list[Detection]
        List of detected objects.
    distance_threshold : float
        Maximum allowed vertical distance between detections to be grouped into the same line.

    Returns
    -------
    list[list[Detection]]
        A list of groups, where each group represents a line of detections.
    """
    return group_detections(detections, Axis.VERTICAL, distance_threshold)


def get_columns(detections: list[Detection], distance_threshold: float) -> list[list[Detection]]:
    """
    Groups detections into vertical columns based on a horizontal distance threshold.

    Parameters
    ----------
    detections : list[Detection]
        List of detected objects.
    distance_threshold : float
        Maximum allowed horizontal distance between detections to be grouped into the same column.

    Returns
    -------
    list[list[Detection]]
        A list of groups, where each group represents a column of detections.
    """
    return group_detections(detections, Axis.HORIZONTAL, distance_threshold)


def sort_axis(detections: list[Detection], axis: Axis) -> list[Detection]:
    """
    Sorts a list of detections along the specified axis.

    Parameters
    ----------
    detections : list[Detection]
        List of detected objects.
    axis : Axis
        Axis along which the detections should be sorted (VERTICAL or HORIZONTAL).

    Returns
    -------
    list[Detection]
        The sorted list of detections.
    """
    key_func = (lambda d: d.bounding_box.p_min.y) if axis == Axis.VERTICAL else (lambda d: d.bounding_box.p_min.x)
    return sorted(detections, key=key_func)


def group_detections(detections: list[Detection], axis: Axis, distance_threshold: float) -> list[list[Detection]]:
    """
    Groups detections along a specified axis using a distance threshold.
    As the threshold increases, fewer groups will be created.

    Parameters
    ----------
    detections : list[Detection]
        List of detected objects.
    axis : Axis
        Axis along which detections should be grouped (VERTICAL or HORIZONTAL).
    distance_threshold : float
        Maximum allowed distance between detections in the same group.

    Returns
    -------
    list[list[Detection]]
        A list of groups, where each group contains detections that are close together along the specified axis.
    """
    if not detections:
        return []

    sorted_detections = sort_axis(detections, axis)
    index = 3 if axis == Axis.VERTICAL else 2  # Selects y-axis (3) or x-axis (2)

    groups = []
    group = [sorted_detections.pop(0)]

    for detection in sorted_detections:
        if detection.bounding_box[index] - group[-1].bounding_box[index] > distance_threshold:
            groups.append(group)
            group = [detection]
        else:
            group.append(detection)

    groups.append(group)
    return groups


def get_selected_balls_index(detections: list[Detection]) -> list[int]:
    """
    Returns the indices of selected balls within the given list of detections.

    Parameters
    ----------
    detections : list[Detection]
        List of detected objects.

    Returns
    -------
    list[int]
        A list of indices where detections are of type `SELECTED_BALL`.
    """
    return [i for i, detection in enumerate(detections) if detection.class_type == Detection.Type.SELECTED_BALL]
