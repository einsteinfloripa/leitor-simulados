from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

import numpy as np
import tflite_runtime.interpreter as tflite
from ultralytics import YOLO

from core.image import CoreImage
from core.detection.base import Detection
from core.definitions import Stage
from core.definitions.question import TestType
from core.definitions.geometry import FloatBoundingBox
from core.IO import MODELS_PATH

from utils.misc import normalize_image



# SECTION: Load function


def load_model(model_path : str, stage : Stage = Stage.NULL) -> DetectionModel:
    """
    Load the model from the given path
    """
    # Convert the path to a Path object
    model_path : Path = Path(model_path)
    
    # Get the model type
    parts = model_path.parts
    model_name = parts[-1]
    
    # Get the type of the model and load accordingly
    model_suffix = model_name.split('.')[-1]
    
    # Legacy model
    if model_suffix == 'tflite':
        interpreter = tflite.Interpreter(
            str(model_path)
        )
        return LegacyModel(interpreter)
    
    # EFScanAlgo model
    elif model_suffix == 'py':
        return EFScanAlgoModel(model_name, stage)
    
    # YOLOV8 model
    elif model_suffix == 'pt':
        engine = YOLO(
            model_path
        )
        return YOLOModel(engine)



# SECTION: Model enum and base class

class ModelType(Enum):
    YOLOV8 = 'YOLOV8'
    LEGACY = 'LEGACY'
    EFSCANALGO = 'EFSCANALGO'

class DetectionModel(ABC):

    def __init__(
            self,
            model_type : ModelType,
            target_stage : Stage = Stage.NULL
        ):
        self.model_type = model_type
        self.target_stage = target_stage

    @abstractmethod
    def detect(self, img : CoreImage) -> list[Detection]:
        pass        



# SECTION: Model classes



# SECTION: YOLOV8 MODEL


class YOLOModel(DetectionModel):
    def __init__(self, engine : YOLO):
        super().__init__(ModelType.YOLOV8)
        self.engine = engine

    def detect(self, img : CoreImage) -> list[Detection]:
        result = self.engine.predict(img.raw, verbose=False)[0]
        detections = []
        boxes = result.boxes.xyxyn.tolist()
        classes = result.boxes.cls.tolist()
        confs = result.boxes.conf.tolist()
        for box, class_id, conf in zip(boxes, classes, confs):
            box = FloatBoundingBox.from_floats(*box)
            detections.append(
                Detection(
                    box,
                    int(class_id),
                    float(conf),
                    img.raw.shape[1],
                    img.raw.shape[0],
                )
            )
        return detections



# SECTION: LEGACY MODEL


class LegacyModel(DetectionModel):
    def __init__(self, interpreter):
        super().__init__(ModelType.LEGACY)
        self.interpreter = interpreter
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


    def detect(self, img : CoreImage) -> list[Detection]:
        normalized_img = normalize_image(
            img.raw, self.input_height, self.input_width
        )
        detections = self.__detect_objects(self.interpreter, normalized_img, img.raw)

        return detections

    # AUX FUNCTIONS

    def __detect_objects(self, interpreter, normalized_image, raw_image):
        self.__set_input_tensor(interpreter, normalized_image)
        interpreter.invoke()

        scores = self.__get_output_tensor(interpreter, 0)
        boxes = self.__get_output_tensor(interpreter, 1)
        count = int(self.__get_output_tensor(interpreter, 2))
        classes = self.__get_output_tensor(interpreter, 3)


        detections = []
        for i in range(count):
            ymin, xmin, ymax, xmax = boxes[i].tolist()
            box = FloatBoundingBox.from_floats(xmin, ymin, xmax, ymax)
            detections.append(
                Detection(
                    box,
                    int(classes[i]),
                    scores[i],
                    raw_image.shape[1],
                    raw_image.shape[0],
                )
            )
        return detections

    def __set_input_tensor(self, interpreter, image):
        tensor_index = interpreter.get_input_details()[0]["index"]
        input_tensor = interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def __get_output_tensor(self, interpreter, index):
        output_details = interpreter.get_output_details()[index]
        tensor = np.squeeze(interpreter.get_tensor(output_details["index"]))
        return tensor



# SECTION: EFSCANALGO MODEL (NO AI)


class EFScanAlgoModel(DetectionModel):
    
    __initialized = False
    __lazy_initialized = False
    __scanner = None
    def __init__(self, name : str, stage : Stage):
        super().__init__(ModelType.EFSCANALGO)
        
        # Set path to import dynamically
        if not self.__initialized:
            self.__init_paths()
        
        # Import the relevant classes to initialize the model
        from EFScanAlgoCore import Scanner
        
        # Initialize static variables
        self.name = name
        self.stage = stage
        
        # Initialize dynamic variables
        self.test = None
    

    ## Lazy explicit initialization ##
    
    def init(self, test : TestType):
        """
        Explicit lazy initialization of the EFScanAlgo model, this must heppen lazily
        because the EFScanAlgo needs to know additional info that can change
        as the user changes the test selected.
        So only when the user selects a test and run the model it is actualy initialized.
        """
        from EFScanAlgoCore import Scanner
        
        # Check if the model is trying to be initialized twice with the same test
        if self.__lazy_initialized and self.test == test:
            return
        
        # Import the relevant classes to initialize the model
        self.__scanner = Scanner(
            self.name,
            test,
            self.stage
        )
        
        # Check if the models target stage is correct
        target_stage = self.__scanner.target_stage
        if target_stage != self.stage:
            raise ValueError(
                f"Model {self.name} is not compatible with stage {self.stage}"
            )
        
        # Stores the state of the model
        self.test = test
        self.__lazy_initialized = True
        

    ## Detection function ##

    def detect(self, img : CoreImage) -> list[Detection]:
        return self.__scanner.detect(img)
        

    # Auxiliar initialization function
    
    def __init_paths(self):
        
        # Include the path to the sys tracked directories
        # ../leinor-simulados/models
        # Include path to models EFscanAlgo
        import sys
        if not MODELS_PATH in sys.path:
            sys.path.append(str(MODELS_PATH.resolve()))
        self.__initialized = True