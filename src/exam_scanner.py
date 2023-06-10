import os
import argparse
import json
import glob
import uuid

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from object_detection import Model, detect_objects_on_img_file, get_bounding_box_pixels

global MODELS_PATH
MODELS_PATH = "/workspace/models"

global IMG_EXTENSIONS
IMG_EXTENSIONS = ("**/*.jpg", "**/*.jpeg", "**/*.png")

global EXPECTED_CPF_BLOCK_COUNT
EXPECTED_CPF_BLOCK_COUNT = 1

global EXPECTED_CPF_COLUMN_COUNT
EXPECTED_CPF_COLUMN_COUNT = 11

global EXPECTED_QUESTIONS_BLOCK_COUNT
EXPECTED_QUESTIONS_BLOCK_COUNT = 6

global EXPECTED_QUESTION_LINE_COUNT
EXPECTED_QUESTION_LINE_COUNT = 10

global EXPECTED_QUESTION_NUMBER_COUNT
EXPECTED_QUESTION_NUMBER_COUNT = EXPECTED_QUESTION_LINE_COUNT

global EXPECTED_QUESTION_SELECTED_BALL_COUNT
EXPECTED_QUESTION_SELECTED_BALL_COUNT = 1


def run_model(
    img,
    detection_model,
    label_map,
    score_threshold,
):
    detections = detect_objects_on_img_file(detection_model, img)

    filtered_detections = []
    for detection in detections:
        if detection["score"] >= score_threshold:
            detection["bounding_box"] = detection["bounding_box"]
            classes_index = int(detection["class_id"])
            detection["class_id"] = label_map[classes_index]
            detection["score"] = float(detection["score"])
            filtered_detections.append(detection)

    return filtered_detections


def approved_1st_stage_detections(detections_1st_stage):
    cpf_block_count = 0
    questions_block_count = 0
    for detection in detections_1st_stage:
        if detection["class_id"] == "cpf_block":
            cpf_block_count += 1
            # TODO: Check if cpf_block is near the top of the page
        if detection["class_id"] == "questions_block":
            questions_block_count += 1
            # TODO: Check if all questions_block have similar width and height
            # TODO: Check if all questions_block are placed in the expected grid (e.g 2 lines and 3 columns)

    if (
        cpf_block_count != EXPECTED_CPF_BLOCK_COUNT
        or questions_block_count != EXPECTED_QUESTIONS_BLOCK_COUNT
    ):
        return False

    return True


def approved_2nd_stage_detections(detections_2nd_stage):
    for detection in detections_2nd_stage:
        if detection["class_id"] == "questions_block":
            # TODO: Check if all question lines have approximately the same width and height
            # TODO: Check if all selected balls have approximately the same height as the average height of the question lines
            # TODO: Check if all selected balls are approximately square. e.g 0.8 <= aspect_ratio <= 1.2
            # TODO: Check if X and Y coordinates of all selected balls make sense in relationship with EXACLY one question line
            # TODO: Check if all question numbers have approximately the same height as the average height of the question lines
            # TODO: Check if X and Y coordinates of all question numbers make sense in relationship with EXACLY one question line
            pass
        if detection["class_id"] == "cpf_block":
            # TODO: .....
            pass

    all_conditions_are_met = True  # TODO: change this to something that represents the results of the validations mentioned above
    if not all_conditions_are_met:
        return False

    return True


def scan_exam(
    model_name_1st_stage,
    model_name_2nd_stage,
    label_map_1st_stage,
    label_map_2nd_stage,
    score_threshold_1st_stage,
    score_threshold_2nd_stage,
    input_directory,
    output_directory,
):
    detection_model_1st_stage = Model(model_name_1st_stage)
    detection_model_2nd_stage = Model(model_name_2nd_stage)

    imgs_paths = []
    for ext in IMG_EXTENSIONS:
        imgs_paths.extend(glob.glob(os.path.join(input_directory, ext), recursive=True))

    if not os.path.exists(
        output_directory
    ):  # TODO check if it makes sense to exit the function in case the dir already exists
        os.makedirs(output_directory)

    for img_path in imgs_paths:
        img = cv2.imread(img_path)
        detections_1st_stage = run_model(
            img,
            detection_model_1st_stage,
            label_map_1st_stage,
            score_threshold_1st_stage,
        )
        if not approved_1st_stage_detections(detections_1st_stage):
            print(
                img_path
            )  # TODO save these img path to a TXT file containing names of images that should be manually reviewed
        else:
            print("1st stage OK!")

        for detection in detections_1st_stage:
            ymin, xmin, ymax, xmax = get_bounding_box_pixels(
                img, detection["bounding_box"]
            )
            cropped_img = img[ymin:ymax, xmin:xmax]
            detections_2nd_stage = run_model(
                cropped_img,
                detection_model_2nd_stage,
                label_map_2nd_stage,
                score_threshold_2nd_stage,
            )
            if not approved_2nd_stage_detections(detections_2nd_stage):
                print(
                    img_path
                )  # TODO save these img path to a TXT file containing names of images that should be manually reviewed
            else:
                print("2nd stage OK!")

        print("")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_1st_stage", type=str, default="1st_stage_v0_0_0")
    parser.add_argument("--model_name_2nd_stage", type=str, default="2nd_stage_v0_0_0")
    parser.add_argument(
        "--label_map_1st_stage",
        type=str,
        nargs="+",
        default=["cpf_block", "questions_block"],
    )
    parser.add_argument(
        "--label_map_2nd_stage",
        type=str,
        nargs="+",
        default=[
            "cpf_column",
            "question_line",
            "selected_ball",
            "unselected_ball",
            "question_number",
        ],
    )
    parser.add_argument("--score_threshold_1st_stage", type=float, default=0.5)
    parser.add_argument("--score_threshold_2nd_stage", type=float, default=0.5)
    parser.add_argument(
        "--input_directory", type=str, default=None, required=True
    )  # TODO: change Default value
    parser.add_argument("--output_directory", type=str, default="detection_output")
    args = parser.parse_args()

    scan_exam(
        args.model_name_1st_stage,
        args.model_name_2nd_stage,
        args.label_map_1st_stage,
        args.label_map_2nd_stage,
        args.score_threshold_1st_stage,
        args.score_threshold_2nd_stage,
        args.input_directory,
        args.output_directory,
    )


if __name__ == "__main__":
    main()
