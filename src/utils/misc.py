import cv2
import numpy as np

def normalize_image(img_raw, detection_model_input_height, detection_model_input_width):
    image_resized = (
        cv2.resize(img_raw, (detection_model_input_height, detection_model_input_width))
        / 255
    )
    img_np = np.expand_dims(image_resized, axis=0).astype(np.float32)

    return img_np

# yolo/prova/nome
# Legacy/Nome
# EFScanAlgo/stage/nome
def parse_model(model_path) -> dict:
    args = model_path.split('/')
    if len(args) == 2:
        return {'type': 'legacy', 'name': args[1]}
    if args[0].lower() == 'yolov8':
        return {'type': args[0], 'name': args[-1], 'test': args[1]}
    return {'type': args[0], 'name': args[-1], 'stage': args[1]}

