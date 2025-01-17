from __future__ import annotations

import inspect
import os
import json

from utils import log
from pathlib import Path

class FileHandler():

    logger = log.get_new_logger("FileHandler")

    INPUT_DIR : Path = None
    OUTPUT_DIR : Path = None
    CROPPED_OUTPUT_DIR : Path = None

    INPUT_PATHS = None
    ACCEPTED_IMAGE_EXTENTIONS = (".jpg", ".jpeg", ".png")

    MODELS_PATH = None
    FIRST_STAGE_MODEL = None
    SECOND_STAGE_MODEL = None

    SAVE_IMAGES = False
    SAVE_YOLO = False

    # Global setters
    @classmethod
    def set_path(cls, attrib, value):
        path = Path(value)
        if path.exists():
            setattr(cls, attrib, path)
        else:
            raise ValueError(f"Path {attrib} : {value} is not valid")

    @classmethod    
    def make_and_set_dir(cls, path_varname, path):
        try:
            path = Path(path)
            if not path.exists():
                path.mkdir()
            setattr(cls, path_varname, path)
        except Exception as e:
            raise e


    @classmethod
    def get_input_paths(cls, recursive=False):
        # Get the caller function name
        caller = os.path.basename(
            inspect.getmodule(inspect.currentframe().f_back).__file__
            )
        # Get the paths from according to the caller function
        if caller == 'build_report.py':
            # Read the status file
            with open(FileHandler.INPUT_DIR  / 'report.txt', 'r') as f:
                status = f.read().strip('\n')
            # Parse the status file
            success, falied = [text.split('\n')[1:] for text in status.split('\n\n\n')]
            # Set input paths
            success_paths = [FileHandler.INPUT_DIR / f'{name}' / f'{name}.json' for name in success] 
            falied_paths = [FileHandler.INPUT_DIR / f'{name}' / f'{name}.json' for name in falied]
            # Create output lists
            return_success = []
            return_falied = []
            # Check if the success paths exists
            for path in success_paths:
                if path.exists():
                    cls.logger.info(f"Adding path: {path.resolve()}")
                    return_success.append(path)
                else:
                    cls.logger.error(f"Path: {path.resolve()} does not exist")
            # Check if the falied paths exists
            for path in falied_paths:
                if path.exists():
                    cls.logger.info(f"Adding path: {path.resolve()}")
                    return_falied.append(path)
                else:
                    cls.logger.error(f"Path: {path.resolve()} does not exist")
            # Return the paths
            return {'success': return_success, 'falied': return_falied}
        # Get the paths from according to the caller function
        elif caller == 'exam_scanner.py':
            try:
                # Check if the input path is a valid file
                if not cls.INPUT_DIR.is_dir():
                    path = str(cls.INPUT_DIR.resolve())
                    if path.endswith(cls.ACCEPTED_IMAGE_EXTENTIONS):
                        cls.logger.info(f"Adding path: {path}")
                        cls.INPUT_PATHS = [path]
                    return
                # The path is a dir
                # Get all the images paths in the input dir, recursive or not
                cls.INPUT_PATHS = [] 
                for extention in cls.ACCEPTED_IMAGE_EXTENTIONS:
                    if recursive:
                        for p in cls.INPUT_DIR.rglob(f"*{extention}"):
                            cls.logger.info(f"Adding path: {p}")
                            cls.INPUT_PATHS.append(str(p))
                    else:
                        for p in cls.INPUT_DIR.glob(f"*{extention}"):
                            cls.logger.info(f"Adding path: {p}")
                            cls.INPUT_PATHS.append(str(p))     
            except Exception as e:
                raise e


    @classmethod
    def save(cls, main_img=None, cropped_imgs=None):
        # Check if the main_img and cropped_imgs are set
        if main_img is None or cropped_imgs is None:
            raise Exception(f"main_img and cropped_imgs must be set, not: {main_img}, {cropped_imgs}")
        # Get the output path
        out_path = cls.OUTPUT_DIR / main_img.name[:-4]
        # Create dir if needed
        out_path.mkdir(parents=True, exist_ok=True)
        cls.logger.info(f"saving {main_img.name} json data : {out_path}")
        # Get the detection data on the right format
        detection_data = {}
        for crop_img in cropped_imgs:
            detection_data.update({crop_img.name: crop_img.to_json()})
        # Save the json data
        with open(str(out_path) + f'/{main_img.name[:-4]}.json', 'w') as f:
            json.dump(detection_data, f, indent=4)

        # If SAVE_IMGS is set, save the images
        if cls.SAVE_IMAGES:
            # Draw the bounding boxes and save the main image
            main_img.draw_bounding_boxes()
            main_img.save(str(out_path / main_img.name))
            cls.logger.info(f"saving {main_img.name} images : {out_path}")
            # Draw the bounding boxes and save the cropped images
            for crop_img in cropped_imgs:
                cls.logger.debug(f"saving {crop_img.name} : {out_path}")
                crop_img.draw_bounding_boxes()
                crop_img.save(str(out_path / crop_img.name))
        
        # If SAVE_YOLO is set, save the yolo format
        if cls.SAVE_YOLO:
            # Get the detections in yolo format
            text = ''
            text += main_img.to_yolo()
            # Save the main image detections txt file
            with open(str(out_path) + f'/{main_img.name[:-4]}.txt', 'w') as f:
                f.write(text)
            # Get and save the cropper detections txt file
            for crop_img in cropped_imgs:
                text = ''
                text += crop_img.to_yolo()
                with open(str(out_path) + f'/{crop_img.name[:-4]}.txt', 'w') as f:
                    f.write(text)
            
                
    
    
    # Smaller Aux functions
    @classmethod
    def txt_out(cls, text, filename, outpath=None):
        if not outpath:
            outpath = cls.OUTPUT_DIR / filename
        with open(outpath, "w") as f:
            f.write(text)
        
    # Function only ment for the build_report.py
    @classmethod
    def save_report(cls, report):
        cls.logger.info(f"saving report: {(cls.OUTPUT_DIR / 'final_report.json').resolve()}	")
        with open(cls.OUTPUT_DIR / 'final_report.json', 'w') as f:
            json.dump(report, f)
