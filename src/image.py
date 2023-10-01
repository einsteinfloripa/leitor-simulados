import uuid

import cv2
import numpy as np

from object_detection import Detection, detect_objects_on_img_file
from filesystem import FileSystem

class Image():

    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255)]

    def __init__(self, path) -> None:
        self.name : str = path.split("/")[-1]
        self.raw : np.ndarray = cv2.imread(path)
        self.detections : list[Detection] | None = None
        
        self.height : int = self.raw.shape[0]
        self.width : int = self.raw.shape[1]

    
    def _has_detections(func):
        def wrapper(self, *args, **kwargs):
            if self.detections is None:
                raise Exception("Image detections not set")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    
    
    def make_detections_with_model(self, model):
        self.detections = detect_objects_on_img_file(model, self.raw)

    @_has_detections
    def save_cropped(self):
        for detection in self.detections:
            ymin, xmin, ymax, xmax = detection.to_pixels()
            cv2.imwrite( 
                str(
                    FileSystem.CROPPED_OUTPUT_DIR / 
                    f"{self.name}_{uuid.uuid4()[:4]}_{detection.class_id}.jpg"
                ),
                self.raw[ymin:ymax, xmin:xmax] 
            )

    @_has_detections
    def draw_bounding_boxes(self):
        for detection in sorted(self.detections):
            ymin, xmin, ymax, xmax = detection.to_pixels()
            cv2.rectangle(self.raw, (xmin, ymin), (xmax, ymax), self.colors[detection.class_id], 3)

    def save(self):
        FileSystem.save_json(self.detections, self.name)
        cv2.imwrite(str(FileSystem.OUTPUT_DIR / self.name), self.raw)

