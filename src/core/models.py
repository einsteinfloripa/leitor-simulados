from __future__ import annotations

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from ultralytics import YOLO

from core.object_detection import Detection
from utils.filehandler import FileHandler
from utils.data_classes import FloatBoundingBox
from utils import normalize_image



def load_model(model_name : str):
    prefix = model_name.split('.')[-1]
    if prefix == 'pt':
        model = YOLO(str(
            FileHandler.MODELS_PATH / 'YoloV8' / model_name
        ))
        return YOLOModel(model)
    else:
        interpreter = tflite.Interpreter(
            str(FileHandler.MODELS_PATH / 'Legacy' / model_name / "saved_model" / "model.tflite")
        )
        return LegacyModel(interpreter)


### YOLOV8 MODEL ###

class YOLOModel:
    def __init__(self, model):
        self.model = model

    def detect(self, img_raw) -> list[Detection]:
        result = self.model.predict(img_raw)[0]
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
                    img_raw.shape[1],
                    img_raw.shape[0],
                )
            )
        return detections

### LEGACY MODEL ###

# CLASSES
class LegacyModel:
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


    def detect(self, img_raw) -> list[Detection]:
        normalized_img = normalize_image(
            img_raw, self.input_height, self.input_width
        )
        detections = self.__detect_objects(self.interpreter, normalized_img, img_raw)

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
            try:
                ymin, xmin, ymax, xmax = boxes[i].tolist()
                box = FloatBoundingBox.from_floats(xmin, ymin, xmax, ymax)
                detections.append(
                    Detection(
                        box,
                        classes[i],
                        scores[i],
                        raw_image.shape[1],
                        raw_image.shape[0],
                    )
                )
            except Exception as e:
                print(e)
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

class EFscanAlgo:
    pass