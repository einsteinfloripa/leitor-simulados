from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .label_map import LabelMap

import math
from enum import Enum
from utils.memory import cache_readonly_property    

from core.definitions.geometry import (
    FloatBoundingBox,
    FloatPoint,
    IntPoint,
    IntBoundingBox
)

class Detection:
    """
    The core detection class is meant to store the information of a detections made by a model
    and provide some useful methods to work with it.

    Attributes:
        - bounding_box (FloatBoundingBox): The bounding box of the detection
        - model_assing_id (int):   The id of the class assigned by the model
    as each model must starts at index 0 and since there are two stages some detections
    may have the same id but represent different classes as they are from different stages. 
        - score (float): The score of confidence of the detection
        - img_width (int): The width of the image where the detection was made. Be aware
    that if the detection was made in a cropped image the width should be the width of 
    the cropped image.
        - img_height (int): The height of the image where the detection was made. Same as
    the width.
        - class_type (Detection.Type): The type of the detection. A unique identifier for each
    class of detection.

    Class Attributes:
        - __label_map: A map tha is used to define the type of the detection based
        on an integer returned by the model. This map is set by the method set_label_map
    """

    class Type(Enum):
        # Null detection
        NULL = -1
        #First stage
        CPF_BLOCK = 0
        QUESTION_BLOCK = 1
        #Second stage
        CPF_COLUMN = 2
        QUESTION_LINE = 3
        SELECTED_BALL = 4
        UNSELECTED_BALL = 5
        QUESTION_NUMBER = 6
        QUESTION_COLUMN = 7

    __label_map : LabelMap = None

    def __init__(
            self,
            bounding_box : FloatBoundingBox,
            model_assing_id : int,
            score : float,
            img_width : int,
            img_height : int,
            anchored_at : IntPoint | None = None
        ) -> None:
        # Check if label map is set
        if Detection.__label_map is None:
            raise Exception("Label map not set")
        # Variables
        self.bounding_box : FloatBoundingBox = bounding_box
        self.model_assing_id : int = model_assing_id
        self.score : float = float(score)
        self.img_width : int =  img_width
        self.img_height : int = img_height
        self.class_type : Detection.Type = self.__label_map.detections[model_assing_id]
        # Lazy initialized by the CoreImage class
        self.anchored_at : IntPoint | None = anchored_at
        self.global_pixel_bounding_box : IntBoundingBox = None
        

    # Public Setters && getters
    @classmethod
    def set_label_map(cls, label_map : LabelMap) -> None:
        cls.__label_map = label_map
    @classmethod
    def get_label_map(cls) -> LabelMap:
        return cls.__label_map

    # Properties
    @cache_readonly_property
    def middle_point(self) -> FloatPoint:
        return FloatPoint(
            (self.bounding_box.p_min.x + self.bounding_box.p_max.x) / 2,
            (self.bounding_box.p_min.y + self.bounding_box.p_max.y) / 2,
        )
    
    @cache_readonly_property
    def pixel_middle_point(self) -> IntPoint:
        return IntPoint(
            int(self.middle_point.x * self.img_width),
            int(self.middle_point.y * self.img_height)
        )

    @cache_readonly_property
    def width(self) -> float:
        return self.bounding_box.p_max.x - self.bounding_box.p_min.x

    @cache_readonly_property
    def height(self) -> float:
        return self.bounding_box.p_max.y - self.bounding_box.p_min.y
    
    @cache_readonly_property
    def pixel_width(self) -> int:
        return int(self.width * self.img_width)
    
    @cache_readonly_property
    def pixel_height(self) -> int:
        return int(self.height * self.img_height)

    @cache_readonly_property
    def xyxy(self) -> tuple[float]:
        return (self.bounding_box.p_min, self.bounding_box.p_max)

    @cache_readonly_property
    def xywh(self) -> tuple[FloatPoint,float,float]:
        return (*self.middle_point, self.width, self.height)

    @cache_readonly_property
    def aspect_ratio(self) -> float:
        return (
            ((self.bounding_box.p_max.y - self.bounding_box.p_min.y) * self.img_height) /
            ((self.bounding_box.p_max.x - self.bounding_box.p_min.x)  * self.img_width)
        )


    ## Operational functions ##

    def rotate(self, angle, origin = None) -> None:
        """
        Rotate the detection by a given angle in degrees

        Args:
        - angle : float
            The angle in degrees to rotate the detection
        - origin : tuple[float, float]
            The origin of the rotation. The default is the center of the detection.
        """
        # Set the origin
        if origin is None: origin = (.5, .5)
        
        # Rotate the bounding box
        angle = math.radians(angle)
        iw, ih = origin
        x1, y1, = self.bounding_box.p_min
        
        # Transform to a system with origin at the center of the image
        y1 = ih - y1
        x1 -= iw
        
        # Rotate the detection
        x1_ = x1 * math.cos(angle) - y1 * math.sin(angle)
        y1_ = x1 * math.sin(angle) + y1 * math.cos(angle)
        
        # Transform back to the original system (i.e. origin in the top left corner)
        y1_ = ih - y1_
        x1_ += iw
        
        # Update values
        sw, sh = self.width, self.height
        self.bounding_box.p_min = FloatPoint(x1_, y1_)
        self.bounding_box.p_max = FloatPoint(x1_ + sw, y1_ + sh)
        
        # Free old cached properties
        self.__free_cache()


    ## Export functions ##
    
    def to_pixels(self) -> IntBoundingBox:
        """
        Return the pixel coordinates of the bounding box in relation to the image
        where the detection was made (cropped or not)
        """
        xmin, ymin, xmax, ymax = self.bounding_box

        xmin = int(xmin * self.img_width)
        xmax = int(xmax * self.img_width)
        ymin = int(ymin * self.img_height)
        ymax = int(ymax * self.img_height)

        return IntBoundingBox.from_ints(xmin, ymin, xmax, ymax)
    

    def to_global_pixels(self) -> IntBoundingBox:
        """
        Return the pixel coordinates of the bounding box in relation to the global image
        """
        if self.anchored_at is None:
            raise Exception("Detection is not in a cropped image")
        # get the coordinate in pixels in r1elation to the cropped image
        xmax = int(self.bounding_box.p_max.x * self.img_width)
        xmin = int(self.bounding_box.p_min.x * self.img_width)
        ymax = int(self.bounding_box.p_max.y * self.img_height)
        ymin = int(self.bounding_box.p_min.y * self.img_height)
        if self.anchored_at:
            xmin += self.anchored_at.x
            ymin += self.anchored_at.y
            xmax += self.anchored_at.x
            ymax += self.anchored_at.y
        return IntBoundingBox.from_ints(xmin, ymin, xmax, ymax)

    def to_json(self) -> dict:
        p_min, p_max = self.xyxy
        return {
            "class_id": self.class_type,
            "score": self.score,
            "bounding_box": [*p_min, *p_max],
        }
    
    def to_yolo(self) -> str:
        x, y, w, h = self.middle_point.x, self.middle_point.y, self.width, self.height
        return f"{self.model_assing_id} {x} {y} {w} {h}"

    
    ## Magic methods ##

    # sorted from top right to bottom left
    def __lt__(self, other):

        # Check if below entirely from the other
        vert_dist_from_other = self.middle_point.y - other.middle_point.y
        self_height = self.bounding_box.p_max.y - self.bounding_box.p_min.y
        
        # Magic number 0.9 is the coeficient to allow an minor sobreposition
        # of detections and still be considered below 
        if abs(vert_dist_from_other) > self_height * 0.9:
            if vert_dist_from_other < 0:
                return True
            else:
                return False
        
        # check if right entirely from the other
        hor_dist_from_other = self.middle_point.x - other.middle_point.x
        self_width = self.bounding_box.p_max.x - self.bounding_box.p_min.x
        # same magic number as above
        if abs(hor_dist_from_other) > self_width * 0.9:
            if hor_dist_from_other < 0:
                return True
            else:
                return False
        # Untie
        if vert_dist_from_other >= hor_dist_from_other:
            return self.middle_point.y < other.middle_point.y
        else:
            return self.middle_point.x < other.middle_point.x
    
    def __repr__(self) -> str:
        return "{}_{:.2f}-{:.2f}-{:.2f}-{:.2f}".format(
            self.class_type.name.lower(), *[x for x in self.bounding_box]
        )
    

    ## Memory management ##
    
    def __free_cache(self):
        """
        Delete all the cached properties of the detection

        *The _cached_properties attribute is created by the cache_readonly_property
        in the __get__ method. See the utils/memory.py for more information.
        """
        if hasattr(self, "_cached_properties"):
            for prop in self._cached_properties:
                prop.invalidate(self)






