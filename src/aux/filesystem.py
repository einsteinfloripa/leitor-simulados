from pathlib import Path
import json

import glob


class FileSystem:

    INPUT_DIR = None
    OUTPUT_DIR = None
    CROPPED_OUTPUT_DIR = None

    INPUT_PATHS = None
    ACCEPTED_IMAGE_EXTENTIONS = (".jpg", ".jpeg", ".png")

    MODELS_PATH = None


    @classmethod
    def set_path(cls, attrib, value):
        setattr(cls, attrib, Path(value))

    @classmethod    
    def get_valid_dir(cls, path_varname, path):
        path = Path(path)
        if not path.exists():
            path.mkdir()
        setattr(cls, path_varname, path)

    @classmethod
    def get_input_paths(cls, recursive=False):
        if str(cls.INPUT_DIR.resolve()).endswith(cls.ACCEPTED_IMAGE_EXTENTIONS):
            cls.INPUT_PATHS = [str(cls.INPUT_DIR.resolve())]
            return
        try:
            cls.INPUT_PATHS = [] 
            for extention in cls.ACCEPTED_IMAGE_EXTENTIONS:
                if recursive:
                    cls.INPUT_PATHS.extend(
                        sorted(glob.glob(f"{cls.INPUT_DIR}/**/*{extention}", recursive=True))
                    )
                else:
                    cls.INPUT_PATHS.extend(
                        sorted(glob.glob(f"{cls.INPUT_DIR}/*{extention}"))
                    )          
        except Exception as e:
            raise e
        
    @classmethod
    def save_json(cls, detections, image_name):
        json_data = []
        if detections:
            for detection in detections:
                json_data.append(detection.to_json())
        with open(cls.OUTPUT_DIR / f"{image_name[:-4]}.json", "w") as f:
            json.dump(json_data, f, indent=4)
    