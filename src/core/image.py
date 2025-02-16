# for Image.get_cropped type hinting
from __future__ import annotations
from core.builder.data_structs import TestBlocks, Block

import cv2
import numpy as np

from core.detection import Detection, DetectionContainer
from definitions.geometry import IntPoint



class Image():
    """
    Image class is used to represent an image with its detections and cropped subregions.

    Attributes:
    - raw: The raw image data.
    - name: The name of the image as in the file.
    - detections: A list of detections in the image.
    - height: The height of the image.
    - width: The width of the image.
    - crops: A list of cropped subregions of the image.
    - cropped_from: The image that this image was cropped from.
    - cropped_from_detection: The type of detection that this image was cropped from.
    - anchored_at: The point where the image was cropped from the original image.
    - order: The order of the image in the cropped image list.
    - BOUNDING_BOXES_DRAWN: A flag that indicates if the bounding boxes were drawn in the image.
    """
    
    @classmethod
    def from_path(cls, path : str):
        """
        Constructor that creates an Image object from a file path.
        """
        name : str = path.split("/")[-1]
        raw : np.ndarray = cv2.imread(path)
        detections : list[Detection] | None = None
        return cls(name, raw, detections)
    

    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255), (255,0,255), (0,0,0)]

    def __init__(
            self,
            name,
            raw,
            detections,
            cropped_from = None,
            cropped_from_detection=None,
            anchored_at : IntPoint | None = None,
            order : int = -1
            ) -> None:
        self.raw : np.ndarray = raw
        self.name : str = name
        self.detections : list[Detection] = detections
        self.height : int = raw.shape[0]
        self.width : int = raw.shape[1]
        self.crops : list[Image] = []
        # Those variable are for the cropped images
        self.cropped_from : Image = cropped_from
        self.cropped_from_detection : Detection = cropped_from_detection
        self.anchored_at : IntPoint = anchored_at
        self.order : int = order
        # Flags
        self.BOUNDING_BOXES_DRAWN = False

    
    def _has_detections(func):
        def wrapper(self, *args, **kwargs):
            if self.detections is None:
                raise Exception("Image detections not set")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    
    def make_detections_with_model(self, model, score_threshold) -> None:
        detections = model.detect(self)
        # Filter detections by score
        self.detections = [d for d in detections if d.score > score_threshold]
        # If the image is a crop, then add the ancor point to the detections
        if self.anchored_at:
            for detection in self.detections:
                detection.anchored_at = self.anchored_at
                detection.global_pixel_bounding_box = detection.to_global_pixels()
        else:
            for detection in self.detections:
                detection.global_pixel_bounding_box = detection.to_pixels()
        # sort and mark detections from top left to bottom right    
        self.detections.sort()

        for i, detection in enumerate(self.detections):
            detection.order = i
        self.BOUNDING_BOXES_DRAWN = False
    
    @_has_detections
    def make_cropped(self) -> list[Image]:
        if not self.detections:
            return False
        cropped = []
        # the detections are sorted by top left to bottom right
        cont = 0
        current_class = self.detections[0].class_type
        for detection in self.detections:
            if detection.class_type != current_class:
                cont = 0
                current_class = detection.class_type
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cropped.append(
                Image(
                    f"{self.name[:-4]}_{detection.class_type.name.lower()}_{cont:02}.jpg",
                    self.raw[ymin:ymax, xmin:xmax],
                    None,
                    cropped_from = self,
                    cropped_from_detection = detection,
                    anchored_at = IntPoint(xmin, ymin),
                    order = cont
                )
            )
            cont += 1
        self.crops = cropped
        return True
            
    @_has_detections
    def draw_bounding_boxes(self) -> None:
        if self.BOUNDING_BOXES_DRAWN: return
        for detection in self.detections:
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cv2.rectangle(self.raw, (xmin, ymin), (xmax, ymax), self.colors[detection.class_id], 3)

    def save(self, path : str) -> None:      
        cv2.imwrite(path + self.name, self.raw)
    
    def to_json(self, only_ball_detections=True) -> list:
        if only_ball_detections:
            json_data = []
            for detection in self.detections:
                if 'ball' in detection.class_name:
                    json_data.append(detection.to_json())
            return json_data
        else:
            json_data = []
            if self.detections:
                for detection in self.detections:
                    json_data.append(detection.to_json())
            return json_data
    
    def to_yolo(self) -> str:
        yolo = '\n'.join([detection.to_yolo() for detection in self.detections])
        return yolo
    
    def to_block(self) -> TestBlocks | Block:
        # Check if is the root image
        # if not return a block
        if self.cropped_from:
            return Block(
                root_detection = self.cropped_from_detection,
                order = self.order,
                container = DetectionContainer(self.detections)
            )
        # else create a TestBlocks object
        cpf_block = None
        questions_blocks = []
        for crop in self.crops:
            block = crop.to_block()
            if block.root_detection.class_type == Detection.Type.CPF_BLOCK:
                cpf_block = block
            else:
                questions_blocks.append(block)
        questions_blocks.sort(key=lambda b: b.order)
        # Return the object
        return TestBlocks(
            name = self.name,
            cpf_block = cpf_block,
            questions_blocks = questions_blocks
        )
        
    def update_from_cache(
            self,
            crops : list[Image],
            detections : list[Detection]
        ) -> None:
        self.crops = crops
        self.detections = detections