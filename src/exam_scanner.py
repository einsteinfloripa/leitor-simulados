import argparse
import checks

from core.object_detection import Detection
from core.image import Image
from core.models import load_model
from utils.filehandler import FileHandler
from utils import log
from utils.misc import parse_model

logger = log.get_new_logger('exam scanner')


def exam_scanner(
    prova,
    model_name_1st_stage,
    model_name_2nd_stage,
    label_map_1st_stage,
    label_map_2nd_stage,
    score_threshold_1st_stage,
    score_threshold_2nd_stage,
    continue_on_fail,
    debug
):
    # Control variables
    falied_imgs = ''
    success_imgs = ''
    # Parse the model names
    fs_config = {'test': prova[0], 'stage': 'FIRST_STAGE', 'cf': continue_on_fail}
    fs_config['model'] = parse_model(model_name_1st_stage)
    ss_config = {'test': prova[0], 'stage': 'SECOND_STAGE', 'cf': continue_on_fail}
    ss_config['model'] = parse_model(model_name_2nd_stage)
    # Load the models
    detection_model_1st_stage = load_model(fs_config)
    detection_model_2nd_stage = load_model(ss_config)

    # Main loop through the images
    for img_path in FileHandler.INPUT_PATHS:

        # Get first stage detections
        Detection.set_label_map(label_map_1st_stage)
        img = Image.from_path(img_path)
        try:
            img.make_detections_with_model(
                detection_model_1st_stage, score_threshold_1st_stage
            )
        except Exception as e:
            if debug: logger.exception(e)
            if continue_on_fail:
                falied_imgs += f'{img.name[:-4]}\n'
                continue
            else:
                exit(1)

        # Perform First stage checks
        if checks.perform(img, stage=1) == 'failed':
            falied_imgs += f'{img.name[:-4]}\n'
            continue
        # Get second stage detections for each cropped image
        Detection.set_label_map(label_map_2nd_stage)
        img.make_cropped()
        for crop_img in img.crops:
            try:
                crop_img.make_detections_with_model(
                    detection_model_2nd_stage, score_threshold_2nd_stage
                )
            except Exception as e:
                if debug: logger.exception(e)
                if continue_on_fail:
                    falied_imgs += f'{img.name[:-4]}\n'
                    continue
                else:
                    exit(1)
            # Perform Second stage checks 
            if checks.perform(crop_img, stage=2) == 'failed':
                falied_imgs += f'{img.name[:-4]}\n'
                continue
        # If all checks passed, tag the img as 'success'
        success_imgs += f'{img.name[:-4]}\n'
        # Call save function, the save setting are set in FileHandler
        FileHandler.save(main_img=img, cropped_imgs=img.crops)
    # Write the scan report
    report = f'success:\n{success_imgs}\n\nfalied:\n{falied_imgs}'
    logger.info(report)
    FileHandler.txt_out(report, 'report.txt')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-mf", "--model_first_stage", type=str, default="EFscanAlgo/first_stage/ef_algo_default.py")
    parser.add_argument("-ms", "--model_second_stage", type=str, default="EFscanAlgo/second_stage/ef_algo_default.py")
    parser.add_argument(
        "-lf",
        "--label_map_1st_stage",
        type=str,
        nargs="+",
        default=["cpf_block", "questions_block"],
    )
    parser.add_argument(
        "-ls",
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
    parser.add_argument("-stf", "--score_threshold_1st_stage", type=float, default=0.5)
    parser.add_argument("-sts", "--score_threshold_2nd_stage", type=float, default=0.5)
    parser.add_argument(
        "-i", "--input_directory", type=str, required=True
    )
    parser.add_argument("-o", "--output_directory", type=str, default="scanner_output")
    # make a log file
    # the arg must be one of the levels of the log 
    # ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument(
        "--logfile",
        nargs="*",
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="make a log file with the specified level defined",
        )
    # remove the detections that do not pass the checks before performing the checks
    parser.add_argument(
        "-fd", "--filter_detections", action="store_true",
        help="remove invalid/out of place detections before performing the checks",
    )
    parser.add_argument(
        "-p",
        "--prova",
        type=str,
        default="SIMUENEM",
        required=True,
        nargs=1,
        choices=['PS', 'SIMUENEM', 'SIMUFSC'],
        help="choose the exam type",
    )
    # for recursive search in the files
    parser.add_argument(
        "-r", "--recursive", action="store_false", default=True,
        help="search for images in all folders inside the input directory",
    )
    # save the image with detections drawn and the detections json file
    parser.add_argument(
        "-si","--save_images", action="store_true", default=False,
        help="save the image with detections drawn",
        )
    # continue the execution even if a check fails
    parser.add_argument(
        "-cf", "--continue_on_fail", action="store_true", default=False,
        help="continue the execution even if a check fails",
    )
    # Add an option to save the detections in Yolo format (id, x, y, w, h)
    parser.add_argument(
        "-yl", "--yolo", action="store_true", default=False,
        help="save the detections in Yolo format (id, x, y, w, h)",
    )
    # Add an option to debug
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False,
        help="print debug information",
    )
    args = parser.parse_args()

    # SETTING GLOBALS
    checks.FILTER_DETECTIONS = args.filter_detections
    checks.CONTINUE_ON_FAIL = args.continue_on_fail
    checks.load_checker(args.prova[0])
    # LOGGING
    if args.logfile is not None:
        try:
            log.set_log_level(args.logfile)
        except ValueError:
            log.set_log_level(['INFO'])
    else: log.remove_filehandler()

    # FILE HANDLER
    FileHandler.set_path( "MODELS_PATH", './models' )
    FileHandler.set_path("INPUT_DIR", args.input_directory)
    FileHandler.make_and_set_dir("OUTPUT_DIR", args.output_directory)
    FileHandler.get_input_paths(recursive=args.recursive)
    FileHandler.SAVE_IMAGES = args.save_images
    FileHandler.SAVE_YOLO = args.yolo
    FileHandler.set_path("FIRST_STAGE_PATH", FileHandler.MODELS_PATH / args.model_first_stage)
    FileHandler.set_path("SECOND_STAGE_PATH", FileHandler.MODELS_PATH / args.model_second_stage)


    exam_scanner(
        args.prova,
        args.model_first_stage,
        args.model_second_stage,
        args.label_map_1st_stage,
        args.label_map_2nd_stage,
        args.score_threshold_1st_stage,
        args.score_threshold_2nd_stage,
        args.continue_on_fail,
        args.debug
    )


if __name__ == "__main__":
    main()
