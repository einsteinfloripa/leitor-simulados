from __future__ import annotations

import cv2

from EFScanAlgoCore import Scanner
from EFScanAlgoCore.ef_utils import (
    ef_get_tilt,
    DEBUG
)
from core.detection.base import Detection
from core.image import Image
from core.model import load_model
from definitions.geometry import FloatBoundingBox



data = {
    'SELECTET_MAX_VAL': 175,
    'SIMUFSC' : {
            'crop_left':0.23,
            'crop_top':0.108
        }
    }


def init_pipeline(scanner : Scanner, config):
    scanner.legacy = load_model({'model': {
        'type':'Legacy',
        'name':'2nd_stage_v0_0_1',
        'test':'ps'
        }
    })


def detect(scanner : Scanner, img : Image) -> list[Detection]:

    # If is a CPF block use legacy model
    if 'cpf' in img.name:
        return scanner.legacy.detect(img)

    # Set the average detection height
    if not hasattr(scanner, '__init_avg_qb_height__'):
        height = img.cropped_from.height
        detections = img.cropped_from.detections
        scanner.avg_qb_height = int((sum([d.height for d in detections if d.class_name=='questions_block'])*height) / len(detections)-1) # TODO:coount cpfblock
        scanner.__init_avg_qb_height__ = True

    # Get the tilt of the image, this must use the parent img (the full img)
    parent_img_raw = img.cropped_from.raw
    tilt = ef_get_tilt(parent_img_raw)
    # Copy the image
    img_raw = img.raw.copy()
    # Rotate the image
    M = cv2.getRotationMatrix2D((img_raw.shape[1] / 2, img_raw.shape[0] / 2), (-1 * tilt), 1.0)
    img_raw = cv2.warpAffine(img_raw, M, (img_raw.shape[1], img_raw.shape[0]))        
    # Convert to gray scale
    img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)

    return get_question_block(scanner, img_raw, img.name)


def get_question_block(scanner, img_raw, name):

    def get_crop_ammount(img):
        _, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)
        # db.img_out(img, f"get_crop_ammount_{name}")
        for i in range(img.shape[0]-1, 0, -1):
            # get the first 3 consecutive lines with a combined mean value of less than 100
            if img[i].mean() < 254:
                return img.shape[0] - i
        return 0


    # If the image has a unexpected aspect ratio, 
    # crop the botton part till it has the expected aspect ratio
    if img_raw.shape[0] > scanner.avg_qb_height*1.1:
        # Find the line that separates the question block from the rest of the image
        # and crop the image to that point
        c_img = img_raw.copy()
        cropp_amount = get_crop_ammount(c_img)
        img_raw = img_raw[:img_raw.shape[0]-cropp_amount, :]

    # Apply a gaussian blur to the image
    img_raw = cv2.GaussianBlur(img_raw, (5, 5), 0)
    # Apply a threshold to the image
    _, img_raw = cv2.threshold(img_raw, 200, 255, cv2.THRESH_BINARY)


    # Crop the image as so only the area with the balls are left
    test = scanner.config['test']
    crop_left = int(img_raw.shape[1] * data[test]['crop_left'])
    crop_top = int(img_raw.shape[0] * data[test]['crop_top'])
    crop = img_raw[crop_top:, crop_left:]


    # Partition the image into 20 parts and get the average pixel value of each part
    # Draw the lines
    for i in range(1, 10):
        y = int(crop.shape[0] * (i / 10))
        cv2.line(crop, (0, y), (crop.shape[1], y), (0, 255, 0), 2)


    # Iterate over each partition saving the coordenates and getting the average pixel value
    first_col  = []
    second_col = []
    min_first_col_idx = 0
    min_second_col_idx = 0
    rows = scanner.get_test_data('qb_rows')
    cols = scanner.get_test_data('qb_cols')
    for j in range(cols):
        low_avg = 999
        for i in range(rows):
            x1 = int(j * crop.shape[1] / cols)
            x2 = int((j + 1) * crop.shape[1] / cols)
            y1 = int(i * crop.shape[0] / rows)
            y2 = int((i + 1) * crop.shape[0] / rows)
            part = crop[y1:y2, x1:x2]
            avg = int(part.mean())

            if j == 0:
                if avg < low_avg:
                    min_first_col_idx = i
                    low_avg = avg
                first_col.append((x1, y1, x2, y2, avg))
            else:
                if avg < low_avg:
                    min_second_col_idx = i
                    low_avg = avg
                second_col.append((x1, y1, x2, y2, avg))
    
    img_raw = cv2.cvtColor(img_raw, cv2.COLOR_GRAY2BGR)
    # Map the detection boxes back to the original image
    # and create the Detection objects
    detections = []
    for q_index, col in [
            (min_first_col_idx, first_col),
            (min_second_col_idx, second_col)
        ]:
        for i, box in enumerate(col):
            x1, y1, x2, y2, avg = box
            if avg > data['SELECTET_MAX_VAL'] and i == q_index:
                crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
                return []
            
            x1 += crop_left
            y1 += crop_top
            x2 += crop_left
            y2 += crop_top


            detections.append(Detection(
                FloatBoundingBox.from_floats(
                    x1/img_raw.shape[1],
                    y1/img_raw.shape[0],
                    x2/img_raw.shape[1],
                    y2/img_raw.shape[0]
                ),
                2 if i == q_index and avg <= data['SELECTET_MAX_VAL'] else 3,
                1,
                img_raw.shape[1],
                img_raw.shape[0]
        ))

    return detections
