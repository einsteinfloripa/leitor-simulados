from definitions.geometry import Axis

from ..detection import Detection

def get_lines(
        detections : list[Detection],
        distance_threshold : float
    ) -> list[list[Detection]]:
    return group_detections(detections, Axis.VERTICAL, distance_threshold)


def get_columns(
        detections : list[Detection],
        distance_threshold : float
    ) -> list[list[Detection]]:
    return group_detections(detections, Axis.HORIZONTAL, distance_threshold)


def sort_axis(detections : list[Detection], axis : Axis) -> list[Detection]:
    if axis == Axis.VERTICAL:
        return sorted(detections, key=lambda d: d.bounding_box.p_min.y)
    elif axis == Axis.HORIZONTAL:
        return sorted(detections, key=lambda d: d.bounding_box.p_min.x)


def group_detections(
        detections : list[Detection],
        axis : Axis,
        distance_threshold : float,
    ) -> list[list[Detection]]:
    """
    This function groups the detections in the given axis using the distance_threshold
    as the distance_threshold gets greater, fewer groups will be created.
    """
    # Sort the detections in the given axis
    sorted_detections = sort_axis(axis, detections)
    # Select the index of the axis to be used
    index = 3 if axis == Axis.VERTICAL else 2
    # Group the detections
    groups = []
    group = [sorted_detections.pop(0)]
    while len(sorted_detections) > 0:
        last_inserted = group[-1]
        next_detection = sorted_detections[0]
        if next_detection.bounding_box[index] - last_inserted.bounding_box[index]\
                > distance_threshold:
            groups.append(group)
            group = [sorted_detections.pop(0)] 
        else:
            group.append(sorted_detections.pop(0))
    groups.append(group)

    return groups

    
def get_selected_balls_index(
        detections : list[Detection],
    ) -> list[int]:
    # Get the selected ball position
    indices = []
    for i, detection in enumerate(detections):
        if detection.class_type == Detection.Type.SELECTED_BALL:
            indices.append(i)
    return indices
