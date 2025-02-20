from dataclasses import dataclass

from core.image import CoreImage
from core.detection import DetectionContainer
from core.definitions.blocks import TestBlocks
from core.definitions.question import TestQuestions


@dataclass
class ImageCacheStruct:
    """
    Data structure to store imformation about an image.

    Attributes:

    - img_name : str
        Name of the image.
    - container : DetectionContainer
        Helper container to store the detections.
    - blocks : TestBlocks
        A First stage detection and the second stage detection inside of it.
    - questions : TestQuestions
        The questions and answers and the cpf of the owner of the image.
    """
    img_name : str
    container : DetectionContainer
    blocks : TestBlocks = None
    questions : TestQuestions = None

