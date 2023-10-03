import argparse
import json
import uuid

import cv2

from object_detection import Model, Detection, detect_objects_on_img_file
from filesystem import FileSystem
import checks

def run_model(
    img,
    detection_model,
    score_threshold,
)-> list[Detection]:
    detections = detect_objects_on_img_file(detection_model, img)

    filtered_detections = []
    for detection in detections:
        if detection.score >= score_threshold:
            filtered_detections.append(detection)
    
    return filtered_detections


def approved_1st_stage_detections(detections_1st_stage : list[Detection]):

    checks.dispatch_detections(detections_1st_stage, stage=1)
    report = checks.get_report()

    #print just for debugging
    for class_name, checks_ in report.items():
            print(class_name.upper().center(80, '-'))
            for check_type in checks_:
                line = f'{list(check_type.keys())[0]}: |'.rjust(40)
                for results in check_type.values():
                    for result_type, result in results.items():
                        line += f'{result_type}={str(result):.10}|'.ljust(10)
                print(line)
    exit()
            
    #     if detection.class_id == 2: # questions_block
    #         questions_block_count += 1
    #         # TODO: Check if all questions_block have similar width and height
    #         # TODO: Check if all questions_block are placed in the expected grid (e.g 2 lines and 3 columns)

    # # if (
    # #     cpf_block_count != EXPECTED_CPF_BLOCK_COUNT
    # #     or questions_block_count != EXPECTED_QUESTIONS_BLOCK_COUNT
    # # ):
    # #   return False

    # return True


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

    Detection.label_map = label_map_1st_stage
    for img_path in FileSystem.INPUT_PATHS:
        img = cv2.imread(img_path)
        detections_1st_stage = run_model(
            img,
            detection_model_1st_stage,
            score_threshold_1st_stage,
        )
        if not approved_1st_stage_detections(detections_1st_stage):
            print(
                img_path
            )  # TODO save these img path to a TXT file containing names of images that should be manually reviewed
        else:
            print("1st stage OK!")
        Detection.label_map = label_map_2nd_stage
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
