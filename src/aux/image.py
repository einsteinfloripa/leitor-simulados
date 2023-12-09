# for Image.get_cropped type hinting
from __future__ import annotations

import uuid

import cv2
import numpy as np

from aux.object_detection import Detection, detect_objects_on_Image_object
from aux.filesystem import FileSystem

class Image():

    @classmethod
    def from_path(cls, path : str):
        name : str = path.split("/")[-1]
        raw : np.ndarray = cv2.imread(path)
        detections : list[Detection] | None = None
        return cls(name, raw, detections)

    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255), (255,0,255), (0,0,0)]

    def __init__(self, name, raw, detections) -> None:
        self.raw : np.ndarray = raw
        self.name : str = name
        self.detections : list[Detection] = detections
        self.height : int = raw.shape[0]
        self.width : int = raw.shape[1]

    
    def _has_detections(func):
        def wrapper(self, *args, **kwargs):
            if self.detections is None:
                raise Exception("Image detections not set")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    
    
    def make_detections_with_model(self, model, score_threshold) -> None:
        detections = detect_objects_on_Image_object(model, self.raw)
        self.detections = [d for d in detections if d.score > score_threshold]

    @_has_detections
    def save_cropped(self):
        for detection in self.detections:
            ymin, xmin, ymax, xmax = detection.to_pixels()
            cv2.imwrite( 
                str(
                    FileSystem.CROPPED_OUTPUT_DIR / 
                    f"{self.name}_{str(uuid.uuid4()[:4])}_{detection.class_id}.jpg"
                ),
                self.raw[ymin:ymax, xmin:xmax] 
            )
    
    @_has_detections
    def get_cropped(self) -> list[Image]:
        cropped = []
        for n, detection in enumerate(self.detections):
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cropped.append(
                Image(
                    f"{self.name[:-4]}_{str(uuid.uuid4())[:4]}_{detection.class_id}.jpg",
                    self.raw[ymin:ymax, xmin:xmax],
                    None
                )
            )
        return cropped
            

    @_has_detections
    def draw_bounding_boxes(self) -> None:
        for detection in sorted(self.detections):
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cv2.rectangle(self.raw, (xmin, ymin), (xmax, ymax), self.colors[detection.class_id], 3)

    def save(self) -> None:
        FileSystem.save_json(self.detections, self.name)
        cv2.imwrite(str(FileSystem.OUTPUT_DIR / self.name), self.raw)

