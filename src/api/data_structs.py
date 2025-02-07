from dataclasses import dataclass

from core.image import Image
from core.detection import DetectionContainer
from core.builder.data_structs import TestBlocks
from definitions.question import TestQuestions


@dataclass
class ImageCacheStruct:
    container : DetectionContainer
    crops : list[Image]
    blocks : TestBlocks = None
    questions : TestQuestions = None

