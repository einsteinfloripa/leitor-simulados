import argparse
import checks

from aux.filehandler import FileHandler
from aux.object_detection import Model, Detection
from aux.image import Image
from aux import log

logger = log.get_new_logger('exam scanner')


def scan_exam(
    model_name_1st_stage,
    model_name_2nd_stage,
    label_map_1st_stage,
    label_map_2nd_stage,
    score_threshold_1st_stage,
    score_threshold_2nd_stage,
):
    falied_imgs = ''
    success_imgs = ''
    detection_model_1st_stage = Model(model_name_1st_stage)
    detection_model_2nd_stage = Model(model_name_2nd_stage)

    
    for img_path in FileHandler.INPUT_PATHS:
        status = 'success'
        try:
            Detection.set_label_map(label_map_1st_stage)
            img = Image.from_path(img_path)

            img.make_detections_with_model(
                detection_model_1st_stage, score_threshold_1st_stage
            )
            if checks.perform(img, stage=1) == 'failed':
                falied_imgs += f'{img.name[:-4]}\n'
                status = 'failed'
                continue
            
            
            Detection.set_label_map(label_map_2nd_stage)
            cropped_imgs : list[Image] = img.get_cropped()

            for crop_img in cropped_imgs:
                crop_img.make_detections_with_model(
                    detection_model_2nd_stage, score_threshold_2nd_stage
                )
                if checks.perform(crop_img, stage=2) == 'failed' and status == 'success':
                    falied_imgs += f'{img.name[:-4]}\n'
                    status = 'failed'
                    continue


            if status == 'success':
                success_imgs += f'{img.name[:-4]}\n'
        except Exception as e:
            logger.exception(e)
            exit(1)
        
        FileHandler.save(main_img=img, cropped_imgs=cropped_imgs)

    report = f'success:\n{success_imgs}\n\nfalied:\n{falied_imgs}'
    logger.info(report)
    FileHandler.txt_out(report, 'report.txt')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-mf", "--model_name_1st_stage", type=str, default="1st_stage_v0_0_0")
    parser.add_argument("-ms", "--model_name_2nd_stage", type=str, default="2nd_stage_v0_0_1")
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
    parser.add_argument("-sf", "--score_threshold_1st_stage", type=float, default=0.5)
    parser.add_argument("-ss", "--score_threshold_2nd_stage", type=float, default=0.5)
    parser.add_argument(
        "-i", "--input_directory", type=str, default='input_images', required=True
    )
    parser.add_argument("-o", "--output_directory", type=str, default="scanner_output")
    # make a log file
    # the arg must be one of the levels of the log 
    # ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument(
        "--logfile",
        nargs="*",
        type=str,
        default=None,
        )
    # remove the detections that do not pass the checks before performing the checks
    parser.add_argument("-fd", "--filter_detections", action="store_true")
    parser.add_argument(
        "-p",
        "--prova",
        type=str,
        default="ENEM",
        required=True,
        nargs=1
    )
    # for recursive search in the files
    parser.add_argument("--recursive", action="store_false", default=True)
    # save the image with detections drawn and the detections json file
    parser.add_argument("--save_imgs", action="store_true", default=False)
    # continue the execution even if a check fails
    parser.add_argument("--continue_on_fail", action="store_true", default=False)


    args = parser.parse_args()
    

    # SETTING GLOBALS
    checks.FILTER_DETECTIONS = args.filter_detections
    checks.CONTINUE_ON_FAIL = args.continue_on_fail
    checks.load_checker(args.prova[0])

    if args.logfile: log.set_log_level(args.logfile)
    else: log.remove_filehandler()


    FileHandler.set_path( "MODELS_PATH", './models' )
    FileHandler.set_path("INPUT_DIR", args.input_directory)
    FileHandler.make_and_set_dir("OUTPUT_DIR", args.output_directory)
    FileHandler.get_input_paths_checker(recursive=args.recursive)
    FileHandler.SAVE_IMAGES = args.save_imgs



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
