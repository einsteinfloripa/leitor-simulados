from dataclasses import dataclass

from core.image import Image
from core.detection import Detection, DetectionCoords
from core.builder.data_structs import TestBlocks



@dataclass
class ImageCacheStruct:
    detections : list[Detection]
    crops : list[Image]
    blocks : TestBlocks
    coords : list[DetectionCoords]
    coord_to_det_map : dict[DetectionCoords : Detection]
    coord_by_type : dict[Detection.Type : list[DetectionCoords]]
