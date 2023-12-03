import argparse
import json
import uuid

import cv2

from object_detection import Model, Detection
from filesystem import FileSystem
from image import Image
import checks

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
):
    detection_model_1st_stage = Model(model_name_1st_stage)
    detection_model_2nd_stage = Model(model_name_2nd_stage)

    for img_path in FileSystem.INPUT_PATHS:
        Detection.set_label_map(label_map_1st_stage)
        img = Image.from_path(img_path)
        img.make_detections_with_model(
            detection_model_1st_stage, score_threshold_1st_stage
        )
        report = checks.perform(img)

        for label, tests in report.items():
            print(label)
            for test in tests:
                for k, v in test.items():
                    print(f'\t{k} : {v}')

        print("1st stage OK!")
        
        

        Detection.set_label_map(label_map_2nd_stage)
        cropped_imgs : list[Image] = img.get_cropped()

        # exit()
        for crop_img in cropped_imgs:
            crop_img.make_detections_with_model(
                detection_model_2nd_stage, score_threshold_2nd_stage
            )
            report = checks.perform(crop_img)
            crop_img.draw_bounding_boxes()
            crop_img.save()


            for label, tests in report.items():
                print(label)
                for test in tests:
                    for k, v in test.items():
                        print(f'{k:60} : {v}')
            # exit()

        print("2nd stage OK!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_1st_stage", type=str, default="1st_stage_v0_0_0")
    parser.add_argument("--model_name_2nd_stage", type=str, default="2nd_stage_v0_0_1")
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

    FileSystem.set_path( "MODELS_PATH", './models' ) # FOR DEBUGGING
    # FileSystem.set_path("MODELS_PATH", "/workspace/models")
    FileSystem.get_valid_dir("INPUT_DIR", args.input_directory)
    FileSystem.get_valid_dir("OUTPUT_DIR", args.output_directory)
    FileSystem.get_input_paths(recursive=True)

    scan_exam(
        args.model_name_1st_stage,
        args.model_name_2nd_stage,
        args.label_map_1st_stage,
        args.label_map_2nd_stage,
        args.score_threshold_1st_stage,
        args.score_threshold_2nd_stage,
    )


if __name__ == "__main__":
    main()
