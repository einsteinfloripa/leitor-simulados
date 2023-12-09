from pathlib import Path
import json

import glob


class FileSystem:

    INPUT_DIR : Path = None
    OUTPUT_DIR : Path= None
    CROPPED_OUTPUT_DIR : Path = None

    INPUT_PATHS = None
    ACCEPTED_IMAGE_EXTENTIONS = (".jpg", ".jpeg", ".png")

    MODELS_PATH = None


    @classmethod
    def set_path_if_exists(cls, attrib, value):
        path = Path(value)
        if path.exists():
            setattr(cls, attrib, path)
        else:
            raise ValueError(f"Path {attrib} : {value} is not valid")

    @classmethod    
    def assure_valid_dir(cls, path_varname, path):
        try:
            path = Path(path)
            if not path.exists():
                path.mkdir()
            setattr(cls, path_varname, path)
        except Exception as e:
            raise e

    @classmethod
    def get_input_paths(cls, recursive=False):
        try:
            if not cls.INPUT_DIR.is_dir():
                path = str(cls.INPUT_DIR.resolve())
                if path.endswith(cls.ACCEPTED_IMAGE_EXTENTIONS):
                    cls.INPUT_PATHS = [path]
                return
            
            cls.INPUT_PATHS = [] 
            for extention in cls.ACCEPTED_IMAGE_EXTENTIONS:
                if recursive:
                    cls.INPUT_PATHS.extend(
                        [str(p) for p in cls.INPUT_DIR.rglob(f"*{extention}")]
                )
                else:
                    cls.INPUT_PATHS.extend(
                        [str(p) for p in cls.INPUT_DIR.glob(f"*{extention}")]
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
    