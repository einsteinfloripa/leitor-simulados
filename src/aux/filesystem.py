import json

from aux import log
from pathlib import Path

class FileSystem():

    logger = log.get_new_logger("FileSystem")

    INPUT_DIR : Path = None
    OUTPUT_DIR : Path = None
    CROPPED_OUTPUT_DIR : Path = None

    INPUT_PATHS = None
    ACCEPTED_IMAGE_EXTENTIONS = (".jpg", ".jpeg", ".png")

    MODELS_PATH = None

    SAVE_IMAGES = False


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
        try:
            if not cls.INPUT_DIR.is_dir():
                path = str(cls.INPUT_DIR.resolve())
                if path.endswith(cls.ACCEPTED_IMAGE_EXTENTIONS):
                    cls.logger.debug(f"Adding path: {path}")
                    cls.INPUT_PATHS = [path]
                return
            
            cls.INPUT_PATHS = [] 
            for extention in cls.ACCEPTED_IMAGE_EXTENTIONS:
                if recursive:
                    for p in cls.INPUT_DIR.rglob(f"*{extention}"):
                        cls.logger.debug(f"Adding path: {p}")
                        cls.INPUT_PATHS.append(str(p))
                else:
                    for p in cls.INPUT_DIR.glob(f"*{extention}"):
                        cls.logger.debug(f"Adding path: {p}")
                        cls.INPUT_PATHS.append(str(p))          
        except Exception as e:
            raise e
        
    @classmethod
    def txt_out(cls, text, filename):
        with open(cls.OUTPUT_DIR / filename, "w") as f:
            f.write(text)
    
    @classmethod
    def save(cls, main_img=None, cropped_imgs=None):
        
        if not main_img or not cropped_imgs:
            raise Exception(f"main_img and cropped_imgs must be set, not: {main_img}, {cropped_imgs}")

        out_path = cls.OUTPUT_DIR / main_img.name[:-4]
        out_path.mkdir(parents=True, exist_ok=True)
        cls.logger.info(f"saving {main_img.name} : {out_path}")

        detection_data = {}
        for crop_img in cropped_imgs:
            detection_data.update({crop_img.name: crop_img.to_json()})
        with open(str(out_path) + f'/{main_img.name[:-4]}.json', 'w') as f:
            json.dump(detection_data, f, indent=4)

        if cls.SAVE_IMAGES:
            main_img.draw_bounding_boxes()
            main_img.save(str(out_path / main_img.name))

            for crop_img in cropped_imgs:
                crop_img.draw_bounding_boxes()
                crop_img.save(str(out_path / crop_img.name))



