from dataclasses import dataclass

from core.image import Image
from core.detection import Detection, DetectionCoords


@dataclass
class CacheStruct:
    detections : list[Detection]
    crops : list[Image]
    coords : list[DetectionCoords]
    coord_to_det_map : dict[DetectionCoords : Detection]
    coord_by_type : dict[Detection.Type : list[DetectionCoords]]


class Cache:

    def __init__(self, number_of_images : int):
        self.data : list[CacheStruct] = [None] * number_of_images

    def cache_image(self, index : int, image : Image):
        detections = image.detections
        if not detections:
            return
        
        crops = image.crops
        for crop in crops:
            detections.extend(crop.detections)
        # Build the data structures
        coord_to_det_map = {}
        coord_by_type = {}
        coords = []
        for detection in detections:
            coord = detection.to_coords()
            coord_to_det_map[coord] = detection
            coords.append(coord)
            try:
                coord_by_type[detection.class_type].append(coord)
            except KeyError:
                coord_by_type[detection.class_type] = [coord]
        # Save the data
        self.data[index] = CacheStruct(
            detections,
            crops,
            coords,
            coord_to_det_map,
            coord_by_type
            )
    
    def from_index(self, index : int) -> CacheStruct:
        return self.data[index]
