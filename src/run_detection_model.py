import argparse

from image import Image
from filesystem import FileSystem

from object_detection import Model, Detection


def run_detection_model(
    input_path,
    detection_model,
    label_map,
    score_threshold,
    crop_objects,
):
    img = Image(input_path)

    # THIS IS THE OBJECT CONTAINING ALL DETECTIONS
    img.make_detections_with_model(detection_model)

    if crop_objects:
        img.save_cropped()

    img.draw_bounding_boxes()
    img.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name", type=str, default="1st_stage_v0_0_0"
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

    # Set variables
    FileSystem.set_valid_dir("OUTPUT_DIR", args.output_directory)
    FileSystem.set_valid_dir("INPUT_DIR", args.input_directory)
    if args.crop_objects:
        FileSystem.set_valid_dir("CROPPED_OUTPUT_DIR", f"{args.output_directory}_cropped")
    FileSystem.get_input_paths()
    
    # FileSystem.set_path("MODELS_PATH", "/workspace/models")
    FileSystem.set_path("MODELS_PATH", "./models")

    Detection.label_map = args.label_map

    detection_model = Model(args.model_name)

    for input_path in FileSystem.INPUT_PATHS:
        run_detection_model(
            input_path,
            detection_model,
            args.label_map,
            args.score_threshold,
            args.crop_objects,
        )


if __name__ == "__main__":
    main()
