import os
import argparse
import json
import glob
import uuid

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from object_detection import Model, detect_objects_on_img_file, get_bounding_box_pixels


def crop_objects_on_image(img, detection, output_directory, output_img_file_name):
    ymin, xmin, ymax, xmax = get_bounding_box_pixels(img, detection["bounding_box"])

    class_id = detection["class_id"]
    try:
        cv2.imwrite(
            os.path.join(
                f"{output_directory}_cropped",
                f"{class_id}_{str(uuid.uuid4())[:4]}_{output_img_file_name}",
            ),
            img[ymin:ymax, xmin:xmax],
        )
    except:
        pass


def draw_bounding_box_on_image(img, detection):
    ymin, xmin, ymax, xmax = get_bounding_box_pixels(img, detection["bounding_box"])

    if detection["class_id"] == "cpf_block":
        bounding_box_color = (0, 0, 255)
    elif detection["class_id"] == "questions_block":
        bounding_box_color = (255, 0, 0)

    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), bounding_box_color, 5)


def run_detection_model(
    input_path,
    detection_model,
    label_map,
    score_threshold,
    output_directory,
    crop_objects,
):
    img = cv2.imread(input_path)

    # THIS IS THE OBJECT CONTAINING ALL DETECTIONS
    detections = detect_objects_on_img_file(detection_model, img)

    # FROM THIS POINT FORWARD THE CODE IS JUST AN EXAMPLE OF HOW TO POST-PROCESS THE DETECTIONS
    output_img_file_name = input_path.split("/")[-1]

    filtered_detections = []
    for detection in detections:
        if detection["score"] >= score_threshold:
            detection["bounding_box"] = detection["bounding_box"]
            classes_index = int(detection["class_id"])
            detection["class_id"] = label_map[classes_index]
            detection["score"] = float(detection["score"])
            filtered_detections.append(detection)

            if crop_objects:
                crop_objects_on_image(
                    img, detection, output_directory, output_img_file_name
                )

            draw_bounding_box_on_image(img, detection)

    cv2.imwrite(f"{output_directory}/{output_img_file_name}", img)

    json.dump(
        filtered_detections,
        open(os.path.join(output_directory, f"{output_img_file_name[:-4]}.json"), "w"),
        indent=4,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name", type=str, default="macro_block_detection_v0_0_0"
    )
    parser.add_argument(
        "--label_map",
        type=str,
        nargs="+",
        default=["cpf_block", "questions_block"],
    )
    parser.add_argument("--input_directory", type=str, default=None, required=True)
    parser.add_argument("--output_directory", type=str, default="detection_output")
    parser.add_argument("--score_threshold", type=float, default=0.5)
    parser.add_argument("--crop_objects", action="store_true")
    args = parser.parse_args()

    global MODELS_PATH
    MODELS_PATH = "/workspace/models"

    detection_model = Model(args.model_name)

    input_paths = (
        sorted(glob.glob(f"{args.input_directory}/*.jpg"))
        + sorted(glob.glob(f"{args.input_directory}/*.jpeg"))
        + sorted(glob.glob(f"{args.input_directory}/*.png"))
    )

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    if args.crop_objects and not os.path.exists(f"{args.output_directory}_cropped"):
        os.makedirs(f"{args.output_directory}_cropped")

    for input_path in input_paths:
        run_detection_model(
            input_path,
            detection_model,
            args.label_map,
            args.score_threshold,
            args.output_directory,
            args.crop_objects,
        )


if __name__ == "__main__":
    main()
