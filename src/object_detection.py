import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from filesystem import FileSystem
from data_classes import FloatBoundingBox, FloatPoint

# CLASSES
class Model:
    def __init__(self, model_name):
        self.interpreter = tflite.Interpreter(
            str(FileSystem.MODELS_PATH / model_name / "saved_model" / "model.tflite")
        )
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


class Detection:

    label_map = []

    def __init__(self, bounding_box, class_id, score, img_width, img_height):
        self.bounding_box : FloatBoundingBox = bounding_box
        self.class_id : int = int(class_id)
        self.class_name : str = self.label_map[self.class_id]
        self.score : float = float(score)
        self.img_width : int =  img_width
        self.img_height : int = img_height
    
                            #       ( x, y )
        self.middle_point : FloatPoint = FloatPoint(
            x = (self.bounding_box.ponto_min.x + self.bounding_box.ponto_max.x) / 2, 
            y = (self.bounding_box.ponto_min.y + self.bounding_box.ponto_max.y) / 2,
        )

    # Public Setters
    @classmethod
    def set_label_map(cls, label_map):
        cls.label_map = label_map

    # Public functions
    def to_pixels(self) -> tuple[int]:
        xmin, ymin, xmax, ymax = self.bounding_box

        xmin = int(xmin * self.img_width)
        xmax = int(xmax * self.img_width)
        ymin = int(ymin * self.img_height)
        ymax = int(ymax * self.img_height)

        return xmin, ymin, xmax, ymax

    def to_json(self) -> dict:
        xmin, ymin, xmax, ymax = self.bounding_box
        return {
            "class_id": self.label_map[self.class_id],
            "score": self.score,
            "bounding_box": [*self.bounding_box],
        }
        
        
    # to draw the bounding boxes in the correct order
    def __lt__(self, other):
        return self.class_id < other.class_id
    
    def __repr__(self) -> str:
        return "{}_{}.{}.{}.{}".format(self.class_name, *[str(p) for p in self.to_pixels()])



def normalize_image(img_raw, detection_model_input_height, detection_model_input_width):
    image_resized = (
        cv2.resize(img_raw, (detection_model_input_height, detection_model_input_width))
        / 255
    )
    img_np = np.expand_dims(image_resized, axis=0).astype(np.float32)

    return img_np


# FUNCTIONS
def set_input_tensor(interpreter, image):
    tensor_index = interpreter.get_input_details()[0]["index"]
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
    output_details = interpreter.get_output_details()[index]
    tensor = np.squeeze(interpreter.get_tensor(output_details["index"]))
    return tensor


def detect_objects(interpreter, normalized_image, raw_image):
    set_input_tensor(interpreter, normalized_image)
    interpreter.invoke()

    scores = get_output_tensor(interpreter, 0)
    boxes = get_output_tensor(interpreter, 1)
    count = int(get_output_tensor(interpreter, 2))
    classes = get_output_tensor(interpreter, 3)

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


def detect_objects_on_Image_object(detection_model, img_raw) -> list[Detection]:
    normalized_img = normalize_image(
        img_raw, detection_model.input_height, detection_model.input_width
    )
    detections = detect_objects(detection_model.interpreter, normalized_img, img_raw)

    return detections

