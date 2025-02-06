from __future__ import annotations

import cv2

from EFScanAlgoCore import Scanner
from EFScanAlgoCore.ef_utils import ef_get_tilt
from core.detection.base import Detection
from core.image import Image
from definitions.geometry import FloatBoundingBox

def detect(scanner : Scanner, img : Image) -> list[Detection]:
    # Get the tilt of the image, this must use the parent img (the full img)
    parent_img_raw = img.cropped_from.raw
    tilt = ef_get_tilt(parent_img_raw)
    # Copy the image
    img_raw = img.raw
    img = img_raw.copy() # this overwrites the img variable
    # Rotate the image
    M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), (-1 * tilt), 1.0)
    img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))        
    # Convert to gray scale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Get the relevant parameters
    if img.shape[0] / img.shape[1] < 1: # Is a Cpf_Block
        # Those values are get empirically and are aways a prcentage of the image HEIGHT
        max_r = int(0.06 * img.shape[0])
        min_r = int(0.03 * img.shape[0])
    else: # Is a Question_Block
        max_r = int(0.05  * img.shape[0])
        min_r = int(0.025 * img.shape[0])

    # Apply HoughCircles
    circles = cv2.HoughCircles(
        img, cv2.HOUGH_GRADIENT, 1, 10, param1=50, param2=30, minRadius=min_r, maxRadius=max_r
    )
    if circles is None:
        return []
    else:
        circles = circles[0]
        circle = [c for c in circles]

    # Apply a gaussian blur to the image
    img = cv2.GaussianBlur(img, (5, 5), 0)
    # Apply a threshold to the image
    _, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)
    # Get the average gray value of the circles
    detections = []
    for circle in circles:
        cont = 0
        avg = 0
        x, y, r = [int(c) for c in circle]
        for i in range(x-r, x+r):
            for j in range(y-r, y+r):
                if (i-x)**2 + (j-y)**2 < r**2:
                    try:
                        cont += 1
                        avg += img[j, i]
                    except:
                        pass
        avg = avg / cont

        # If the average is greater than 100, the circle is filled
        if avg > 100:
            id = 3
        else:
            id = 2
        iw, ih = img.shape[1], img.shape[0]
        detections.append( Detection(
            FloatBoundingBox.from_yolo(x/iw, y/ih, 2*r/iw, 2*r/ih),
            id,
            1,
            img.shape[1],
            img.shape[0]
        ))
    # Rotate back the detections
    for detection in detections:
        detection.rotate(tilt)
    
    return detections




