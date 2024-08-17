from __future__ import annotations

import cv2
import math

from EFscanAlgo.ef_defs import Line, Axis
from core.image import Image

### HELPER FUNCTIONS ###

def ef_merge_lines(
        lines : list[Line],
        axis : Axis, 
        img,
        const : float = 0.05
    ):
    # Initial setup
    if axis == Axis.HORIZONTAL:
        lines.sort(key=lambda x: x[1])
    elif axis == Axis.VERTICAL:
        lines.sort(key=lambda x: x[0])
    # Cluster lines together
    groups = ef_group_lines(lines, axis, img, const)
    # Get a average line from the groups
    avg_lines = []
    for group in groups:
        avg_lines.append(ef_avg_lines(group, axis, img))

    return avg_lines

def ef_get_axis_alling_lines(
        lines : list[Line],
        img
    ) -> tuple[list[Line], list[Line]]:
    '''Receive a list of lines and an image and returns the lines that are alligned with the principal axis.'''
    # Initial setup & definitions
    h_lines = []
    v_lines = []
    height, width = img.shape[:2]
    # Filter the lines
    for l in lines:
        # Filter lines with a slope between -88 and -2 or 2 and 88
        if l[2] - l[0] == 0:
            tg = 90.0
        else:
            tg = math.degrees(math.atan((l[3] - l[1]) / (l[2] - l[0])))
        if tg > 4 and tg < 86 or tg < -4 and tg > -86:
            continue
        # filter lines that are above some threshold
        if l[1] > height*0.9 or l[1] < height*0.36 or \
        l[0] > width*0.98 or l[2] < width*0.03:
            continue

        if tg < 45 and tg >= -45: # horizontal
            h_lines.append(l)
        else:
            v_lines.append(l) # vertical
        
    return h_lines, v_lines

def ef_group_lines(
        lines : list[Line],
        axis : Axis,
        img,
        const = 0.05,
        sort = False
    ):
    '''Group lines that are close to each other in the desired axis.'''
    # Sort the lines if needed
    if sort: lines.sort(key=lambda x: x[axis.value])
    spacing = img.shape[axis.value] * const
    groups = []
    for i in range(0, len(lines)):
        if i == 0:
            groups.append([lines[i]])
        elif abs(lines[i][axis.value] - lines[i-1][axis.value]) < spacing:
            groups[-1].append(lines[i])
        else:
            groups.append([lines[i]])

    return groups

def ef_avg_lines(lines : list[Line], axis : Axis, img : Image) -> Line:
    '''Receive a list of lines and returns a line with average values on the chosen axis.'''
    # Get the lenght of the image in the desired axis
    lenght = img.shape[:2][axis.value]
    # Calculate the average of the lines
    avg = [0, 0]
    for line in lines:
        avg[0] += line[axis.value]
        avg[1] += line[axis.value+2]
    avg = [int(x/len(lines)) for x in avg]
    # Put the lines in the right order depending on the axis
    if axis == Axis.HORIZONTAL:
        return Line([0, avg[0], lenght, avg[1]])
    else:
        return Line([avg[0], 0, avg[1], lenght])

def ef_get_tilt(img, draw=False):
    '''Receves an Eintein Floripa test image and returns the tilt of the image.'''
    # Get onlt the top 15% of the image
    img_ = img[0:int(img.shape[0]*0.15), 0:img.shape[1]].copy()
    # Apply a gaussian blur
    img_ = cv2.GaussianBlur(img_, (5, 5), 0)
    # Filter the noise
    img_ = cv2.bilateralFilter(img_, 9, 75, 75)
    # Convert to grayscale
    img_ = cv2.cvtColor(img_, cv2.COLOR_BGR2GRAY)
    # Canny edge detection
    edges = cv2.Canny(img_, 50, 200)
    # Find the contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Identify the squares
    squares = []
    for cnt in contours:
        # Aproximate the contour to a polygon
        epsilon = 0.05 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        # Check if the aproximation has 4 sides and is convex
        if len(approx) == 4 and cv2.isContourConvex(approx):
            (x, y, w, h) = cv2.boundingRect(approx)
            # Check it is a big enough square
            # The magic numbers were obtained by trial and error
            if w > 0.015 * img_.shape[1] and h > 0.076 * img_.shape[0]:
                # Check if the aspect ratio is close to 1
                aspect_ratio = float(w) / h
                if 0.9 <= aspect_ratio <= 1.1:
                    squares.append(approx)
    if len(squares) > 2:
        # Delete smaller squares
        sorted_squares = sorted(squares, key=cv2.contourArea, reverse=True)
        squares = sorted_squares[:2]

    # Find the centers of the squares
    centers = []
    for square in squares:
        M = cv2.moments(square)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centers.append((cX, cY))
    centers.sort(key=lambda x: x[0])
    
    # Draw the squares and centers if needed
    if draw:
        # convert back to BGR
        img_ = cv2.cvtColor(img_, cv2.COLOR_GRAY2BGR)
        for square in squares:
            print(square)
            cv2.drawContours(img_, [square], -1, (0, 255, 0), 3)
        for center in centers:
            print(center)
            cv2.circle(img_, (cX, cY), 5, (255, 0, 0), -1) 
        cv2.imwrite("debug_tilt.jpg", img_)
    

    # Finally calculate the tilt using the centers
    tilt = 0
    if len(squares) == 2:
        tilt = - math.degrees(math.atan( # menos porque o eixo y é invertido
            (centers[1][1] - centers[0][1]) / (centers[1][0] - centers[0][0])
        ))
        return tilt
    else:
        print("Could not find only two squares in the image.")
        return


# DEBUG HELPER DEV CLASS
class DEBUG:

    colors = {
        "red": (0, 0, 255),
        "green": (0, 255, 0),
        "blue": (255, 0, 0),
        "yellow": (0, 255, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0)
    }
    lcolors = list(colors.values())

    def __init__(self):
        import sys
        if 'cv2' not in sys.modules:
            import cv2
    
    def img_out(
            self,
            img,
            save_as = "debug.jpg",
            lines : list[list[Line]] | None = None,
            circles = None,
            thickness = 3
        ):
        cont = 0
        # Draw the lines if needed
        if lines is not None:
            for group in lines:
                for line in group:
                    cv2.line(img, (line[0], line[1]), (line[2], line[3]), self.lcolors[cont], thickness)
                cont += 1
        # Draw the circles if needed
        if circles is not None:
            for group in circles:
                for circle in group:
                    cv2.circle(img, (circle[0], circle[1]), circle[2], self.lcolors[cont], thickness)
                cont += 1
        # Save the image
        cv2.imwrite(save_as, img)