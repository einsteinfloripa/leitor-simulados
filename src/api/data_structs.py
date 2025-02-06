from dataclasses import dataclass

from core.image import Image
from core.detection import DetectionContainer
from core.builder.data_structs import TestBlocks



@dataclass
class ImageCacheStruct:
    container : DetectionContainer
    crops : list[Image]
    blocks : TestBlocks
