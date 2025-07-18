# for Image.get_cropped type hinting
from __future__ import annotations
from typing import Generator
from pathlib import Path

import cv2
import numpy as np

from core.definitions.blocks import TestBlocks, Block
from core.definitions.geometry import IntPoint
from core.detection import Detection, DetectionContainer



class CoreImage():
    """
    CoreImage class is used to represent an image with its detections and cropped subregions.

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
    def from_paths(
            cls,
            paths : list[str],
            lazy = True
        ) -> Generator[CoreImage, None, None]:
        """
        Constructor that creates a generator of CoreImage objects from
        a list of file paths.

        Parameters:
        - paths : list[str]
            A list of file paths.
        - lazy : Bool
            A flag that indicates if the images should be loaded lazily.
        """
        if lazy:
            for path in paths:
                name : str = path.split("/")[-1]
                raw : np.ndarray = cv2.imread(path)
                detections : list[Detection] | None = None
                yield cls(name, raw, detections)
        else:
            return [cls.from_path(path) for path in paths]

    @classmethod
    def from_path(cls, path : str):
        """
        Constructor that creates an CoreImage object from a file path.
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
        self.crops : list[CoreImage] = []
        # Those variable are for the cropped images
        self.cropped_from : CoreImage = cropped_from
        self.cropped_from_detection : Detection = cropped_from_detection
        self.anchored_at : IntPoint = anchored_at
        self.order : int = order

    
    ## Aux decoration functions ##

    def _has_detections(func):
        def wrapper(self, *args, **kwargs):
            if self.detections is None:
                raise Exception("CoreImage detections not set")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    

    ## Detection functions ##

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
    def make_cropped(self) -> list[CoreImage]:
        if not self.detections:
            return False
        cropped = []
        # the detections are sorted by top left to bottom right
        cont = 1
        current_class = self.detections[0].class_type
        for detection in self.detections:
            if detection.class_type != current_class:
                cont = 1
                current_class = detection.class_type
            xmin, ymin, xmax, ymax = detection.to_pixels()
            cropped.append(
                CoreImage(
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
            

    ## Exporting functions ##
    
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
    
    ## Import fucntion ##

    def import_blocks(self, blocks : TestBlocks | Block) -> None:
        
        # Case where is a root image
        if not self.cropped_from:
            if not isinstance(blocks, TestBlocks):
                raise Exception(
                    "Blocks must be a TestBlocks object for a root image"
                )
            
            # Get the first stage detections
            self.detections = [block.root_detection for block in blocks.questions_blocks]
            
            # Make the cropped images
            self.make_cropped()

            # Sort the question blocks
            ordered_blocks = sorted(blocks.questions_blocks, key=lambda b: b.order)
            # Recursively call the function for the cropped images
            for crop in self.crops:
                if crop.cropped_from_detection.class_type == Detection.Type.CPF_BLOCK:
                    crop.import_blocks(blocks.cpf_block)
                else:
                    order = crop.order
                    crop.import_blocks(ordered_blocks[order - 1]) 
                    # -1 because the order starts at 1
        
        # Case where is a cropped image
        else:
            if not isinstance(blocks, Block):
                raise Exception(
                    "Blocks must be a Block object for a cropped image"
                )
            self.detections = blocks.container.get_detections()
                    

    ## Saving fuction ## 

    def save(self, path : Path) -> None:
        out_path = path / self.name     
        cv2.imwrite(str(out_path), self.raw)
    
    ## Memory management functions ##

    def free(self) -> None:
        """
        Recursively frees the memory used by this image and all its 
        cropped sub-images.

        This method breaks both parent-to-child (`crops`) and 
        child-to-parent (`cropped_from`) references to aid garbage collection.
        """
        for crop in self.crops:
            crop.free()
        
        self.raw = None
        self.detections = None

        self.crops = []
        self.cropped_from = None
