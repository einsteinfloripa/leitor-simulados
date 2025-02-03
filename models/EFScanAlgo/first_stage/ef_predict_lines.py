from __future__ import annotations

import math
import cv2

from core.detection import Detection
from core.image import Image
from core.models import load_model
from utils.data_classes import FloatBoundingBox

from EFScanAlgoCore import Scanner
from EFScanAlgoCore.ef_utils import (
    ef_get_tilt,
    ef_get_axis_alling_lines,
    ef_avg_lines,
    ef_merge_lines,
    ef_group_lines,
    ef_avg_group_distance,
    ef_unpack_groups,
    DEBUG
)
from EFScanAlgoCore.ef_defs import Axis, Line


class Configs:

    def getHoughLinesParams(img):
        # Define line sensitivity
        rho = 1
        # Define angle sensitivity
        theta = math.pi / 90
        # Define the threshold
        width = img.shape[1]
        threshold_m_coef = 0.10576
        threshold_c_coef = 30.3
        threshold = round(threshold_m_coef * width + threshold_c_coef)
        # Lines
        lines = None
        # Define the minLineLength
        minLineLength_m_coef = 0.01175
        minLineLength_c_coef = 10.036
        minLineLength = round(minLineLength_m_coef * width + minLineLength_c_coef)
        # Define the maxLineGap
        maxLineGap = 1
        # Return the parameters
        return rho, theta, threshold, lines, minLineLength, maxLineGap


def init_pipeline(scanner : Scanner, config : dict) -> None:
    scanner.yolo = load_model({'model': {
        'type':'yolov8',
        'name':'first_stage.pt',
        'test':'ps'
        }
    })

def detect(scanner : Scanner, img : Image) -> list[Detection]:
    
    img_raw = img.raw
    detections = list()
    detections.extend(__get_question_blocks(scanner, img_raw))
    detections.extend(__get_cpf_blocks(scanner, img))

    return detections


def __get_question_blocks(scanner : Scanner, img_raw):
    db = DEBUG()
    # Get the relevant points for the bounding boxes
    def get_blocks(intersec, img_):
        # Get the relevant constants
        n_boxes = scanner.get_test_data('n_boxes')
        boxes_per_row = scanner.get_test_data('n_boxes_per_row')
        nv = scanner.get_test_data('n_v_lines')
        # Break condition
        bc = 2*n_boxes + (n_boxes//boxes_per_row)*nv

        # Find the bounding boxes
        detections = []
        cont = 0
        while True:
            # Get the indexes
            j = cont % nv
            if j == 0 and cont != 0: 
                cont += nv
            k = cont // nv
            # Break
            if cont >= bc: break
            # Append the bounding box
            detections.append(Detection(
                FloatBoundingBox.from_floats(
                    *intersec[j + nv*k],
                    *intersec[j+1 + nv*(k+1)],
                ),
                1,
                1,
                img_.shape[1],
                img_.shape[0],
                ))
            cont += 2
        
        return detections

    def strip_outer_lines(
        groups,
        axis : Axis,
        img,
        tolerance : float = 0.005
    ):
        # Initial setup
        n = axis.value
        _tolerance = img.shape[n] * tolerance
        # Get the first and last group
        first_group = groups.pop(0)
        last_group = groups.pop(-1)
        # Get the bound coordinates
        lower_bound = sum(
            [(line[n] + line[n+2])/2 for line in first_group]) / len(first_group) - _tolerance
        upper_bound = sum(
            [(line[n] + line[n+2])/2 for line in last_group]) / len(last_group) + _tolerance
        # Set the bounds
        bounds = (lower_bound, upper_bound)
        # Filter the outer lines
        first_group = [line for line in first_group if (line[n]+line[n+2])/2 > bounds[0] and (line[n]+line[n+2])/2 < bounds[1] ]
        last_group = [line for line in last_group if (line[n]+line[n+2])/2 > bounds[0] and (line[n]+line[n+2])/2 < bounds[1] ]
        groups.insert(0, first_group)
        groups.append(last_group)
        return [line for group in groups for line in group]

    # Copy the image
    img = img_raw.copy()
    # Get the image tilt
    tilt = ef_get_tilt(img)
    if tilt is None: return []
    assert tilt != None, "Failed to get tilt from image."
    # Rotate the image
    M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), (-1 * tilt), 1.0)
    img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Filter the noise
    _, gray = cv2.threshold(img, 220, 255, cv2.THRESH_BINARY)
    # Use Canny to detect edges
    edges = cv2.Canny(gray, 50, 200, L2gradient=True)
    # Extract the lines
    lines = [Line(l[0]) for l in cv2.HoughLinesP(edges, *Configs.getHoughLinesParams(img))]
    # Get the axis alling lines
    h_lines, v_lines = ef_get_axis_alling_lines(lines, img)
    # Merge the lines
    h_lines = ef_merge_lines(h_lines, Axis.HORIZONTAL, img, const=0.05)
    v_lines = ef_merge_lines(v_lines, Axis.VERTICAL, img, const=0.003)
    # Group the lines
    h_groups = ef_group_lines(h_lines, Axis.HORIZONTAL, img, const=0.05)
    v_groups = ef_group_lines(v_lines, Axis.VERTICAL, img, const=0.01)
    # Remove the outer lines
    h_lines = strip_outer_lines(h_groups, Axis.HORIZONTAL, img)
    v_lines = strip_outer_lines(v_groups, Axis.VERTICAL, img)
    # Filter the groups and add missing lines
    h_groups = filter_groups(scanner, h_groups, Axis.HORIZONTAL, img)
    v_groups = filter_groups(scanner, v_groups, Axis.VERTICAL, img)
    # Unpack lines
    h_lines = ef_unpack_groups(h_groups, Axis.HORIZONTAL)
    v_lines = ef_unpack_groups(v_groups, Axis.VERTICAL)
    # Perform consistency check
    assert len(h_groups) == scanner.get_test_data('n_rows') + 1, "Number of rows does not match with the expected value."
    assert len(v_groups) == scanner.get_test_data('n_boxes_per_row') + 1, "Number of boxes per row does not match with the expected value."
    # Perform consistency check
    assert len(h_lines) == scanner.get_test_data('n_h_lines'), "Number of horizontal lines does not match with the expected value."
    assert len(v_lines) == scanner.get_test_data('n_v_lines'), "Number of vertical lines does not match with the expected value."
    # find the intersection of the lines
    img_h, img_w = img.shape[:2]
    intersec = []
    for h_line in h_lines:
        for v_line in v_lines:
            intersec.append((v_line[0]/img_w, h_line[1]/img_h))
    # sort the intersections
    intersec = sorted(intersec, key=lambda x: (x[1], x[0]))
    # Get the bounding boxes from the intersections
    detections = get_blocks(intersec, img)
    # Apply the tilt back to the bounding boxes
    for detection in detections:
        detection.rotate(tilt)
    # Return the detections
    return detections

def __get_cpf_blocks(scanner, img):
    # Calls the yolo model to detect the cpf blocks
    detections : list[Detection] = scanner.yolo.detect(img)
    CPFBlocks = []
    # Filter the detections to get only the CPF blocks 
    for detection in detections:
        if detection.model_assing_id == 0:
            CPFBlocks.append(detection)
    return CPFBlocks

def filter_groups(scanner : Scanner, groups : list[Line], axis : Axis, img : Image):

    def new_group(axis, at, avg_dist, dir, single=False, side_line=False):
        dist = scanner.get_test_data('v_line_spacing') if axis == Axis.HORIZONTAL else scanner.get_test_data('h_line_spacing')
        delta = img.shape[axis.counterAxis.value] * dist * dir / 2
        to = at + avg_dist*dir

        if side_line:
            to = to - delta
        if single:
            if axis == Axis.HORIZONTAL:
                return [Line([0, int(to), img.shape[1], int(to)])]
            else:
                return [Line([int(to), 0, int(to), img.shape[0]])]


        if axis == Axis.HORIZONTAL:
            return [
                Line([0, int(to-delta) , img.shape[1], int(to-delta)]),
                Line([0, int(to+delta) , img.shape[1], int(to+delta)])
            ]
        else:
            return [
                Line([int(to-delta), 0, int(to-delta), img.shape[0]]),
                Line([int(to+delta), 0, int(to+delta), img.shape[0]])
            ]

    def internal_distance_ok(group, axis, img):
        if len(group) != 2:
            return False
        img_size = img.shape[axis.value]
        emirical_mesure = scanner.get_test_data('h_line_spacing') if axis == Axis.HORIZONTAL else scanner.get_test_data('v_line_spacing')
        dist = abs(group[0][axis.value] - group[1][axis.value])
        return dist <= round(img_size*emirical_mesure*1.25)


    if axis == Axis.HORIZONTAL:
        avg_dist_empirical = scanner.get_test_data('h_line_spacing')/2 + scanner.get_test_data('box_height')
    else:
        avg_dist_empirical = scanner.get_test_data('v_line_spacing')/2 + scanner.get_test_data('box_width')
        

    avg_dist = avg_dist_empirical*img.shape[axis.counterAxis.value]
    tolerance = avg_dist*0.2

    direction = 0
    if len(groups[0]) == 1:
        direction=1
    elif len(groups[-1]) == 1:
        # Reverse the groups
        groups = groups[::-1]
        direction=-1
    else:
        # TODO: Add another method to find the lines
        raise Exception("Unable to find a starting line.")

    m = scanner.get_test_data('n_boxes_per_row') if axis == Axis.VERTICAL else scanner.get_test_data('n_rows')
    new_groups = []
    p = 0
    q = 1
    while q < m+1:
        gp = groups[p]
        # print(p, q)
        # print([len(q) for q in groups])

        try:
            gq = groups[q]
            dist = abs(ef_avg_lines(gq, axis, img)[axis.value] - ef_avg_lines(gp, axis, img)[axis.value])
        except IndexError:
            dist = float('inf')
        if dist < avg_dist - tolerance:
            # print("remove")
            groups.pop(q)
        elif dist > avg_dist + tolerance:
            # print("add")
            at = ef_avg_lines(gp, axis, img)[axis.value]
            groups.insert(q,new_group(axis, at, avg_dist, direction))
        elif q != m and ((len(gq) != 2) or (len(gq) == 2 and not internal_distance_ok(gq, axis, img))):
            # print("subs")
            groups.pop(q)
            at = ef_avg_lines(gp, axis, img)[axis.value]
            if p == 0:
                groups.insert(q,new_group(axis, at, avg_dist, direction, side_line=True))
            else:
                groups.insert(q,new_group(axis, at, avg_dist, direction))
        else:
            # print("keep")
            new_groups.append(gp)
            p += 1
            q += 1

    while len(groups) > m+1:
        groups.pop(-1)
    last_group = groups[-1]
    if len(last_group) != 1:
        at = ef_avg_lines(groups[-2], axis, img)[axis.value]
        ng = new_group(axis, at, avg_dist, direction, single=True, side_line=True)
        new_groups.append(ng)
    else:
        new_groups.append(groups[-1])

    return new_groups
            

