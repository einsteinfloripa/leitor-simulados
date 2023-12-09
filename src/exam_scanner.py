import argparse
import json
import uuid
import cv2
import checks

from aux.object_detection import Model, Detection
from aux.filesystem import FileSystem
from aux.image import Image
from aux import log


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
        try:
            checks.perform(img, stage=1)
        except AssertionError as e:
            print(e)
            continue
        except Exception as e:
            print('[CRITICAL]', e)
    
        print("1st stage OK!")
        
        
        Detection.set_label_map(label_map_2nd_stage)
        cropped_imgs : list[Image] = img.get_cropped()

        cropped_imgs = [img]

        for crop_img in cropped_imgs:
            crop_img.make_detections_with_model(
                detection_model_2nd_stage, score_threshold_2nd_stage
            )
            try:
                checks.perform(crop_img, stage=2)
            except AssertionError as e:
                log.logging.exception(e)
                continue
            
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
    parser.add_argument("--filter_only", action="store_true")
    parser.add_argument(
        "--prova",
        type=str,
        default="ENEM",
        required=True,
        nargs=1
    )
    parser.add_argument("--recursive", action="store_true", default=True)

    args = parser.parse_args()

    # Set globals
    FileSystem.set_path_if_exists( "MODELS_PATH", './models' ) # FOR DEBUGGING
    # FileSystem.set_path("MODELS_PATH", "/workspace/models")
    FileSystem.set_path_if_exists("INPUT_DIR", args.input_directory)
    FileSystem.assure_valid_dir("OUTPUT_DIR", args.output_directory)
    FileSystem.get_input_paths(recursive=args.recursive)
    checks.FILTER_DETECTIONS = args.filter_detections
    checks.FILTER_ONLY = args.filter_only
    checks.load_checker(args.prova[0])
    if not args.logfile: log.remove_filehandler()


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
