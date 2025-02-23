from dataclasses import dataclass
from typing import Optional

from core.detection import DetectionContainer
from core.definitions.blocks import TestBlocks
from core.definitions.question import TestQuestions

@dataclass
class ImageCacheStruct:
    """
    Data structure to store information about an image and its related detections.

    Parameters
    ----------
    img_name : str
        The name of the image.
    container : DetectionContainer
        A container that holds detected objects or regions within the image.
    blocks : Optional[TestBlocks], default=None
        The first-stage detection results, along with second-stage detections inside it.
    questions : Optional[TestQuestions], default=None
        The extracted questions, answers, and CPF (identification number) of the image owner.
    """

    img_name: str
    container: DetectionContainer
    blocks: Optional[TestBlocks] = None
    questions: Optional[TestQuestions] = None
