import argparse

from aux.image import Image
from aux.filehandler import FileHandler

from aux.object_detection import Model, Detection


def run_detection_model(
    input_path,
    detection_model,
    label_map,
    score_threshold,
    crop_objects,
):
    img = Image.from_path(input_path)

    # THIS IS THE OBJECT CONTAINING ALL DETECTIONS
    img.make_detections_with_model(detection_model, score_threshold)

    if crop_objects:
        img.save_cropped()

    img.draw_bounding_boxes()
    img.save(str(FileHandler.OUTPUT_DIR / img.name))
    detecctions = img.to_json(only_ball_detections=True, for_annotation=True)
    lines = []
    for detection in detecctions:
        id = detection["class_id"]
        if detection['score'] > 0.7 and id == 3:
            x, y, w, h = detection["bbox"]
            lines.append(f"{id} {x} {y} {w} {h}")
    with open(str(FileHandler.OUTPUT_DIR / f"{img.name[:-4]}.txt"), "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name", type=str, default="2nd_stage_v0_0_1"
    )
    parser.add_argument(
        "--label_map",
        type=str,
        nargs="+",
        default=["cpf_column", "question_line", "selected_ball", "unselected_ball", "question_number", "question_column"],
    )
    parser.add_argument("--input_directory", type=str, default=None, required=True)
    parser.add_argument("--output_directory", type=str, default="detection_output")
    parser.add_argument("--score_threshold", type=float, default=0.5)
    parser.add_argument("--crop_objects", action="store_true")
    args = parser.parse_args()

    # Set variables
    FileHandler.make_and_set_dir("OUTPUT_DIR", args.output_directory)
    FileHandler.set_path("INPUT_DIR", args.input_directory)
    if args.crop_objects:
        FileHandler.make_and_set_dir("CROPPED_OUTPUT_DIR", f"{args.output_directory}_cropped")
    FileHandler.get_input_paths_checker()
    
    # FileHandler.set_path("MODELS_PATH", "/workspace/models")
    FileHandler.set_path("MODELS_PATH", "./models") # FOR DEBUGGING

    Detection.label_map = args.label_map

    detection_model = Model(args.model_name)

    for input_path in FileHandler.INPUT_PATHS:
        run_detection_model(
            input_path,
            detection_model,
            args.label_map,
            args.score_threshold,
            args.crop_objects,
        )


if __name__ == "__main__":
    main()
