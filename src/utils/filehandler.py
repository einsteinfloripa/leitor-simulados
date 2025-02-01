
import inspect
import os
import json

from utils import log
from pathlib import Path



class FileHandler():

    logger = log.get_new_logger("FileHandler")

    # Images
    IMAGE_FILES : list[str] = []
    ACCEPTED_IMAGE_EXTENTIONS = {'.png', '.jpg', '.jpeg'}
    ACCEPTED_MODELS_EXTENTIONS = {'.tflite', '.py', '.pb'}
    # Models
    MODELS_PATH = Path(__file__).parent.parent.parent / 'models'

    @classmethod
    def find_image_files(cls, folder_path : str):
        folder = Path(folder_path)
        files = [
            str(f) for f in folder.glob('*.*') \
            if f.suffix.lower() in cls.ACCEPTED_IMAGE_EXTENTIONS
        ]
        return files


      
           

    # @classmethod
    # def save(cls, main_img=None, cropped_imgs=None):
    #     # Check if the main_img and cropped_imgs are set
    #     if main_img is None or cropped_imgs is None:
    #         raise Exception(f"main_img and cropped_imgs must be set, not: {main_img}, {cropped_imgs}")
    #     # Get the output path
    #     out_path = cls.OUTPUT_DIR / main_img.name[:-4]
    #     # Create dir if needed
    #     out_path.mkdir(parents=True, exist_ok=True)
    #     cls.logger.info(f"saving {main_img.name} json data : {out_path}")
    #     # Get the detection data on the right format
    #     detection_data = {}
    #     for crop_img in cropped_imgs:
    #         detection_data.update({crop_img.name: crop_img.to_json()})
    #     # Save the json data
    #     with open(str(out_path) + f'/{main_img.name[:-4]}.json', 'w') as f:
    #         json.dump(detection_data, f, indent=4)

    #     # If SAVE_IMGS is set, save the images
    #     if cls.SAVE_IMAGES:
    #         # Draw the bounding boxes and save the main image
    #         main_img.draw_bounding_boxes()
    #         main_img.save(str(out_path / main_img.name))
    #         cls.logger.info(f"saving {main_img.name} images : {out_path}")
    #         # Draw the bounding boxes and save the cropped images
    #         for crop_img in cropped_imgs:
    #             cls.logger.debug(f"saving {crop_img.name} : {out_path}")
    #             crop_img.draw_bounding_boxes()
    #             crop_img.save(str(out_path / crop_img.name))
        
    #     # If SAVE_YOLO is set, save the yolo format
    #     if cls.SAVE_YOLO:
    #         # Get the detections in yolo format
    #         text = ''
    #         text += main_img.to_yolo()
    #         # Save the main image detections txt file
    #         with open(str(out_path) + f'/{main_img.name[:-4]}.txt', 'w') as f:
    #             f.write(text)
    #         # Get and save the cropper detections txt file
    #         for crop_img in cropped_imgs:
    #             text = ''
    #             text += crop_img.to_yolo()
    #             with open(str(out_path) + f'/{crop_img.name[:-4]}.txt', 'w') as f:
    #                 f.write(text)

