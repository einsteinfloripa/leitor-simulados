import cv2
import numpy as np

def normalize_image(img_raw, detection_model_input_height, detection_model_input_width):
    image_resized = (
        cv2.resize(img_raw, (detection_model_input_height, detection_model_input_width))
        / 255
    )
    img_np = np.expand_dims(image_resized, axis=0).astype(np.float32)

    return img_np

# .../models/yolo/prova/nome
# .../models/Legacy/Nome
# .../models/EFScanAlgo/stage/nome
def parse_model(model_path) -> dict:
    # Check if the model path is a model path
    if 'models' not in model_path:
        return
    # Get the relevant parts of the path
    _, endpath = model_path.split('models')
    endpath.strip('/')
    args = endpath.split('/')
    # Parse the model path
    if args[0].lower() == 'legacy':
        return {'type': 'legacy', 'name': args[1]}
    if args[0].lower() == 'yolov8':
        return {'type': 'yolov8', 'name': args[-1], 'test': args[1]}
    return {'type': 'efscanalgo', 'name': args[-1], 'stage': args[1]}

