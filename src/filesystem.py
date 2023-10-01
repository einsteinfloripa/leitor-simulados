from pathlib import Path
import json

import glob


class FileSystem:

    INPUT_DIR = None
    OUTPUT_DIR = None
    CROPPED_OUTPUT_DIR = None

    INPUT_PATHS = None

    MODELS_PATH = None


    @classmethod
    def set_path(cls, attrib, value):
        setattr(cls, attrib, Path(value))

    @classmethod    
    def set_valid_dir(cls, path_varname, path):
        path = Path(path)
        if not path.exists():
            path.mkdir()
        setattr(cls, path_varname, path)

    @classmethod
    def get_input_paths(cls):
        if not hasattr(cls, "INPUT_DIR"):
            raise Exception("Input paths not set!")
        try:
            cls.INPUT_PATHS = (
                sorted(glob.glob(f"{cls.INPUT_DIR}/*.jpg"))
                + sorted(glob.glob(f"{cls.INPUT_DIR}/*.jpeg"))
                + sorted(glob.glob(f"{cls.INPUT_DIR}/*.png"))
            )
        except Exception as e:
            raise e
        
    @classmethod
    def save_json(cls, detections, image_name):
        json_data = []
        for detection in detections:
            json_data.append(detection.to_json())
        with open(cls.OUTPUT_DIR / f"{image_name[:-4]}.json", "w") as f:
            json.dump(json_data, f, indent=4)
    