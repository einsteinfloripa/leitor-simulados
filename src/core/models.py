from __future__ import annotations
from abc import ABC, abstractmethod

import numpy as np

from ultralytics import YOLO
import tflite_runtime.interpreter as tflite

from core.detection import Detection
from core.image import Image
from core.defs import Stage, TestType, PATH_SEPARATOR
from utils.data_classes import FloatBoundingBox
from utils.misc import normalize_image
from utils.filehandler import FileHandler

def load_model(model_path : str, stage : Stage = Stage.NULL) -> DetectionModel:
    """
    Load the model from the given path
    """
    # Get the model type
    parts = list(model_path.split(PATH_SEPARATOR))
    model_name = parts[-1]
    # Get the type of the model and load accordingly
    model_suffix = model_name.split('.')[-1]
    # Legacy model
    if model_suffix == 'tflite':
        interpreter = tflite.Interpreter(
            model_path
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


class ModelType:
    YOLOV8 = 'YOLOV8'
    LEGACY = 'LEGACY'
    EFSCANALGO = 'EFSCANALGO'

class DetectionModel(ABC):

    def __init__(self, model_type : ModelType):
        self.model_type = model_type

    @abstractmethod
    def detect(self, img : Image) -> list[Detection]:
        pass        


### YOLOV8 MODEL ###

class YOLOModel(DetectionModel):
    def __init__(self, engine : YOLO):
        super().__init__(ModelType.YOLOV8)
        self.engine = engine

    def detect(self, img : Image) -> list[Detection]:
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

### LEGACY MODEL ###

# CLASSES
class LegacyModel(DetectionModel):
    def __init__(self, interpreter):
        super().__init__(ModelType.LEGACY)
        self.interpreter = interpreter
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


    def detect(self, img : Image) -> list[Detection]:
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


### NON AI MODEL ###

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
        from EFScanAlgoCore import Scanner, Config
        # Initialize static variables
        self.name = name
        self.stage = stage
        # Initialize dynamic variables
        self.test = None
    
    def init(self, test : TestType):
        """
        Explicit lazy initialization of the EFScanAlgo model, this must heppen lazily
        because the EFScanAlgo needs to know additional info that can change
        as the user changes the test selected.
        So only when the user selects a test and run the model it is actualy initialized.
        """
        from EFScanAlgoCore import Scanner, Config
        # Check if the model is trying to be initialized twice with the same test
        if self.__lazy_initialized and self.test == test:
            # No need to initialize again
            return
        # Import the relevant classes to initialize the model
        config = Config(
            model_name = self.name,
            test = test,
            stage = self.stage
        )
        self.__scanner = Scanner(config)
        # Stores the state of the model
        self.test = test
        self.__lazy_initialized = True
        

    def detect(self, img : Image) -> list[Detection]:
        return self.__scanner.detect(img)
        

    # Initialization function
    def __init_paths(self):
        import sys
        # Include the path to the sys tracked directories
        # ../leinor-simulados/models
        # Include path to models EFscanAlgo
        sys.path.append(str(FileHandler.MODELS_PATH))
        self.__initialized = True