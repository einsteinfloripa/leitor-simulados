import os
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

global MODELS_PATH
MODELS_PATH = "/workspace/models"


class Model:
    def __init__(self, model_name):
        self.interpreter = tflite.Interpreter(
            os.path.join(MODELS_PATH, model_name, "saved_model", "model.tflite")
        )
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]["shape"]
        self.input_height = input_details[1]
        self.input_width = input_details[2]


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


def detect_objects(interpreter, image):
    set_input_tensor(interpreter, image)
    interpreter.invoke()

    scores = get_output_tensor(interpreter, 0)
    boxes = get_output_tensor(interpreter, 1)
    count = int(get_output_tensor(interpreter, 2))
    classes = get_output_tensor(interpreter, 3)

    detections = []
    for i in range(count):
        try:
            result = {
                "bounding_box": boxes[i].tolist(),
                "class_id": classes[i],
                "score": scores[i],
            }
            detections.append(result)
        except:
            pass
    return detections


def detect_objects_on_img_file(detection_model, img_raw):
    normalized_img = normalize_image(
        img_raw, detection_model.input_height, detection_model.input_width
    )

    detections = detect_objects(detection_model.interpreter, normalized_img)

    return detections


def get_bounding_box_pixels(img, bounding_box):
    ymin, xmin, ymax, xmax = bounding_box
    img_height, img_width, _ = img.shape

    xmin = int(xmin * img_width)
    xmax = int(xmax * img_width)
    ymin = int(ymin * img_height)
    ymax = int(ymax * img_height)

    return [ymin, xmin, ymax, xmax]
