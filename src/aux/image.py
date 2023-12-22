# for Image.get_cropped type hinting
from __future__ import annotations

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

    def __init__(self, name, raw, detections, cropped_by = None) -> None:
        self.raw : np.ndarray = raw
        self.name : str = name
        self.detections : list[Detection] = detections
        self.height : int = raw.shape[0]
        self.width : int = raw.shape[1]
        self.cropped_by : str | None = cropped_by
        self.BOUNDING_BOXES_DRAWN = False

    
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
        # sort and mark detections from top left to bottom right    
        self.detections.sort()
        for i, detection in enumerate(self.detections):
            detection.order = i
        self.BOUNDING_BOXES_DRAWN = False
    
    @_has_detections
    def get_cropped(self) -> list[Image]:
        cropped = []
        # the detections are sorted by top left to bottom right
        cont = 0
        current_class = self.detections[0].class_id
        for detection in self.detections:
            if detection.class_id != current_class:
                cont = 0
                current_class = detection.class_id
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cropped.append(
                Image(
                    f"{self.name[:-4]}_{detection.class_name}_{cont:02}.jpg",
                    self.raw[ymin:ymax, xmin:xmax],
                    None,
                    cropped_by=detection.class_name
                )
            )
            cont += 1
        return cropped
            
    @_has_detections
    def draw_bounding_boxes(self) -> None:
        if self.BOUNDING_BOXES_DRAWN: return
        for detection in self.detections:
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cv2.rectangle(self.raw, (xmin, ymin), (xmax, ymax), self.colors[detection.class_id], 3)

    def save(self, path : str) -> None:      
        cv2.imwrite(path, self.raw)
    
    def to_json(self) -> list:
        json_data = []
        if self.detections:
            for detection in self.detections:
                json_data.append(detection.to_json())
        return json_data
