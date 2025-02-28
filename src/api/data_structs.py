from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from core.definitions.blocks import TestBlocks
from core.definitions.question import TestQuestions
from core.definitions.enums import ModelType, Stage
from core.detection import DetectionContainer, LabelMap
from core.IO import MODELS_PATH

__all__ = [ 'ImageCacheStruct', 'ModelInfo' ]

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


from pathlib import Path
from typing import Optional

class ModelInfo:
    """
    Data structure to store and provide information about a model.
    
    Attributes
    ----------
    name : str
        The name of the model.
    model_type : ModelType
        The type of the model (e.g., LEGACY, EFSCANALGO, YOLOV8).
    target_stage : Stage
        The target stage of the model (e.g., FIRST, SECOND, BOTH, or NULL).
    rel_path : str
        The relative path to the model file.
    detection_parameters : Optional[DetectionParameters]
        Additional detection parameters (if any).
    """

    @classmethod
    def from_models_path(cls, path: str):
        """
        Create a ModelInfo object from a model file path.

        Parameters
        ----------
        path : str
            The path to the model file.

        Returns
        -------
        ModelInfo
            A ModelInfo object containing extracted model details.
        """
        fullpath = Path(path)
        rel_path = fullpath.relative_to(MODELS_PATH)

        parts = rel_path.parts
        name, extension = parts[-1].split('.')
        model_type = (
            ModelType.LEGACY if extension == 'tflite'
            else ModelType.EFSCANALGO if extension == 'py'
            else ModelType.YOLOV8
        )
        target_stage = (
            Stage.FIRST if 'first_stage' in path
            else Stage.SECOND if 'second_stage' in path
            else Stage.BOTH if 'single_stage' in path
            else Stage.NULL
        )
        return cls(name, model_type, target_stage, str(rel_path))

    def __init__(
            self,
            name: str,
            model_type: ModelType,
            target_stage: Stage,
            rel_path: str,
        ):
        """
        Initialize a ModelInfo object.

        Parameters
        ----------
        name : str
            The name of the model.
        model_type : ModelType
            The type of the model.
        target_stage : Stage
            The target stage of the model.
        rel_path : str
            The relative path to the model file.
        """
        self.name = name
        self.model_type = model_type
        self.target_stage = target_stage
        self.rel_path = rel_path
    
    def __repr__(self):
        """
        Return a string representation of the ModelInfo object.

        Returns
        -------
        str
            A detailed string representation of the model information.
        """
        return f'ModelInfo(name={self.name}, model_type={self.model_type}, target_stage={self.target_stage}, rel_path={self.rel_path})'

    def __str__(self):
        """
        Return a user-friendly string representation of the model.

        Returns
        -------
        str
            A simple string representation with model name and type.
        """
        return f"{self.name} ({self.model_type.name})"

    def __hash__(self):
        """
        Compute the hash of the ModelInfo object.

        Returns
        -------
        int
            The hash value based on name, model type, and target stage.
        """
        return hash((self.name, self.model_type, self.target_stage))
