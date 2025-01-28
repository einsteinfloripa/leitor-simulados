from enum import Enum

import numpy as np
import cv2

from src.core.detection import Detection, DetectionCoords
from src.core.image import ImageCache


class DrawingContext:

    brg_image_raw : np.ndarray = None
    detection_coords = dict[str : list[DetectionCoords]] = {}
    detection_map : dict[DetectionCoords : Detection] = {}

    ## Getters && Setters ##
    @classmethod
    def has_detections(cls):
        return True if cls.detection_coords else False

    ## Operation Functions ##
    @classmethod
    def build_context(cls, cache : ImageCache, img_raw : np.ndarray):
        # Get all the detections in the image cached data
        detections : list[Detection] = []
        detections.extend(cache.detections)
        cropped_imgs = cache.crops
        for img in cropped_imgs:
            detections.extend(img.detections)
        # Build the detection map
        cls.detection_map = cls.__build_detection_map(detections)
        # Sort and save the detections
        cls.detection_coords = cls.__sort_detection_coords_by_classname(
            detections
        )
        # Build the image for tkinter display
        cls.brg_image_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)

    ## Private Functions ##
    @classmethod
    def __build_detection_map(
                cls,
                detections : list[Detection]
            ) -> dict[DetectionCoords : Detection]:
        # Clear the current detections
        detection_map = {}
        # Convert the detection to DetectionCoords
        # Make a map from DetectionCoords to Detection
        cls.detection_map = {}
        for detection in detections:
            # Convert the detection to DetectionCoords
            coords : DetectionCoords = detection.to_coords()
            # Add the detection to the map
            cls.detection_map[coords] = detection
        return detection_map

    @classmethod
    def __sort_detection_coords_by_classname(
                cls,
                detection_coords : list[DetectionCoords]
            ) -> dict[str,DetectionCoords]:
        # Sort the detection coords by class name
        return_list = {}
        for detection in detection_coords:
            try:
                return_list[detection.class_name].append(detection)
            except KeyError:
                return_list[detection.class_name] = [detection]
        return return_list
