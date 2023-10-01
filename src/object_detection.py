import os
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from filesystem import FileSystem


class Model:
    def __init__(self, model_name):
        self.interpreter = tflite.Interpreter(
            os.path.join(FileSystem.MODELS_PATH, model_name, "saved_model", "model.tflite")
        )
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


class Detection:

    def __init__(self, bounding_box, class_id, score, width, height):
        self.bounding_box : list[float, float, float, float] = bounding_box
        self.class_id : int = int(class_id)
        self.score : float = float(score)
        self.width : int =  width
        self.height : int = height
    
    def to_pixels(self) -> tuple[int, int, int, int]:
        ymin, xmin, ymax, xmax = self.bounding_box
        # print(self.bounding_box, self.width, self.height)

        xmin = int(xmin * self.width)
        xmax = int(xmax * self.width)
        ymin = int(ymin * self.height)
        ymax = int(ymax * self.height)

        return (ymin, xmin, ymax, xmax)

    def to_json(self) -> dict:
        ymin, xmin, ymax, xmax = self.bounding_box
        return {
            "class_id": self.label_map[self.class_id],
            "score": self.score,
            "bounding_box": self.bounding_box,
        }
        

    # to draw the bounding boxes in the correct order
    def __lt__(self, other):
        self.class_id < other.class_id



def normalize_image(img_raw, detection_model_input_height, detection_model_input_width):
    image_resized = (
        cv2.resize(img_raw, (detection_model_input_height, detection_model_input_width))
        / 255
    )
    img_np = np.expand_dims(image_resized, axis=0).astype(np.float32)

    return img_np


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
            detections.append(
                Detection(
                    boxes[i].tolist(),
                    classes[i],
                    scores[i],
                    raw_image.shape[1],
                    raw_image.shape[0],
                )
            )
        except:
            pass
    return detections


def detect_objects_on_img_file(detection_model, img_raw) -> list[Detection]:
    normalized_img = normalize_image(
        img_raw, detection_model.input_height, detection_model.input_width
    )
    detections = detect_objects(detection_model.interpreter, normalized_img, img_raw)

    return detections

