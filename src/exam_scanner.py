import argparse
import json
import uuid
import cv2

from object_detection import Model, Detection
from filesystem import FileSystem
from image import Image
import checks


def scan_exam(
    model_name_1st_stage,
    model_name_2nd_stage,
    label_map_1st_stage,
    label_map_2nd_stage,
    score_threshold_1st_stage,
    score_threshold_2nd_stage,
    logfile,
    filter_detections,
):
    detection_model_1st_stage = Model(model_name_1st_stage)
    detection_model_2nd_stage = Model(model_name_2nd_stage)

    for img_path in FileSystem.INPUT_PATHS:
        Detection.set_label_map(label_map_1st_stage)
        img = Image.from_path(img_path)

        img.make_detections_with_model(
            detection_model_1st_stage, score_threshold_1st_stage
        )
        report = checks.perform(
            img, filter_detections=filter_detections, logfile=logfile
        )
        print("1st stage OK!")
        

        exit()
        Detection.set_label_map(label_map_2nd_stage)
        cropped_imgs : list[Image] = img.get_cropped()

        for crop_img in cropped_imgs:
            crop_img.make_detections_with_model(
                detection_model_2nd_stage, score_threshold_2nd_stage
            )
            report = checks.perform(crop_img)
            crop_img.draw_bounding_boxes()
            crop_img.save()


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
    parser.add_argument("--logfile", action="store_true")
    parser.add_argument("--filter_detections", action="store_true")
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
        args.logfile,
        args.filter_detections,
    )


if __name__ == "__main__":
    main()
