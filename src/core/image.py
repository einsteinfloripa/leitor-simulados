# for Image.get_cropped type hinting
from __future__ import annotations
from dataclasses import dataclass

import cv2
import numpy as np

from core.detection import Detection
from utils.data_classes import IntPoint


@dataclass
class ImageCache:
    detections : list[Detection]
    crops : list[Image]

class Image():
    
    @classmethod
    def from_path(cls, path : str):
        name : str = path.split("/")[-1]
        raw : np.ndarray = cv2.imread(path)
        detections : list[Detection] | None = None
        return cls(name, raw, detections)

    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255), (255,0,255), (0,0,0)]

    def __init__(
            self,
            name,
            raw,
            detections,
            cropped_from = None,
            cropped_from_detection=None,
            anchored_at : IntPoint | None = None
            ) -> None:
        self.raw : np.ndarray = raw
        self.name : str = name
        self.detections : list[Detection] = detections
        self.height : int = raw.shape[0]
        self.width : int = raw.shape[1]
        self.crops : list[Image] = []
        self.BOUNDING_BOXES_DRAWN = False
        # Those variable are for the cropped images
        self.cropped_from : Image = cropped_from
        self.cropped_from_detection = cropped_from_detection
        self.anchored_at : IntPoint = anchored_at

    
    def _has_detections(func):
        def wrapper(self, *args, **kwargs):
            if self.detections is None:
                raise Exception("Image detections not set")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    
    def make_detections_with_model(self, model, score_threshold) -> None:
        detections = model.detect(self)
        # Filter detections by score
        self.detections = [d for d in detections if d.score > score_threshold]
        # If the image is a crop, then add the ancor point to the detections
        if self.anchored_at:
            for detection in self.detections:
                detection.anchored_at = self.anchored_at
        # sort and mark detections from top left to bottom right    
        self.detections.sort()

        for i, detection in enumerate(self.detections):
            detection.order = i
        self.BOUNDING_BOXES_DRAWN = False
    
    @_has_detections
    def make_cropped(self) -> list[Image]:
        if not self.detections:
            return False
        cropped = []
        # the detections are sorted by top left to bottom right
        cont = 0
        current_class = self.detections[0].class_type
        for detection in self.detections:
            if detection.class_type != current_class:
                cont = 0
                current_class = detection.class_type
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cropped.append(
                Image(
                    f"{self.name[:-4]}_{detection.class_type.name.lower()}_{cont:02}.jpg",
                    self.raw[ymin:ymax, xmin:xmax],
                    None,
                    cropped_from=self,
                    cropped_from_detection = detection.class_type,
                    anchored_at=IntPoint(xmin, ymin)
                )
            )
            cont += 1
        self.crops = cropped
        return True
            
    @_has_detections
    def draw_bounding_boxes(self) -> None:
        if self.BOUNDING_BOXES_DRAWN: return
        for detection in self.detections:
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cv2.rectangle(self.raw, (xmin, ymin), (xmax, ymax), self.colors[detection.class_id], 3)

    def save(self, path : str) -> None:      
        cv2.imwrite(path, self.raw)
    
    def to_json(self, only_ball_detections=True) -> list:
        if only_ball_detections:
            json_data = []
            for detection in self.detections:
                if 'ball' in detection.class_name:
                    json_data.append(detection.to_json())
            return json_data
        else:
            json_data = []
            if self.detections:
                for detection in self.detections:
                    json_data.append(detection.to_json())
            return json_data
    
    def to_yolo(self) -> str:
        yolo = '\n'.join([detection.to_yolo() for detection in self.detections])
        return yolo

    def to_cache(self) -> ImageCache:
        """
        This method saves the current state of the image detection and its
        cropped subregions
        """
        # If there are no detections, return None
        if not self.detections:
            return None
        # Dereference the main image reference as it is likely to be deleted
        for crop in self.crops:
            crop.raw = None
            self.cropped_from = None
        return ImageCache(self.detections, self.crops)

    def from_cache(self, cache : ImageCache) -> None:
        """
        This method restores the image state from a cache
        """
        pass
        
        