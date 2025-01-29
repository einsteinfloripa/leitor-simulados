import math
from enum import Enum
from dataclasses import dataclass

from utils.data_classes import FloatBoundingBox, FloatPoint




class Detection:
    """
    The core detection class is meant to store the information of a detections made by a model
    and provide some useful methods to work with it.

    Attrivutes:
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
    """

    class Type(Enum):
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

    __label_map : "LabelMap" = None

    def __init__(
            self,
            bounding_box : FloatBoundingBox,
            model_assing_id : int,
            score : float,
            img_width : int,
            img_height : int
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

    # Public Setters && getters
    @classmethod
    def set_label_map(cls, label_map : "LabelMap") -> None:
        cls.__label_map = label_map
    @classmethod
    def get_label_map(cls) -> "LabelMap":
        return cls.__label_map

    # Properties
    @property
    def middle_point(self) -> FloatPoint:
        return FloatPoint(
            (self.bounding_box.p_min.x + self.bounding_box.p_max.x) / 2,
            (self.bounding_box.p_min.y + self.bounding_box.p_max.y) / 2,
        )

    @property
    def width(self) -> float:
        return self.bounding_box.p_max.x - self.bounding_box.p_min.x

    @property
    def height(self) -> float:
        return self.bounding_box.p_max.y - self.bounding_box.p_min.y

    @property
    def xyxy(self) -> tuple[float]:
        return (self.bounding_box.p_min, self.bounding_box.p_max)

    @property
    def xywh(self) -> tuple[FloatPoint,float,float]:
        return (*self.middle_point, self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        return (
            ((self.bounding_box.p_max.y - self.bounding_box.p_min.y) * self.img_height) /
            ((self.bounding_box.p_max.x - self.bounding_box.p_min.x)  * self.img_width)
        )


    # Operational functions
    def rotate(self, angle, origin = None):
        # Set the origin
        if origin is None: origin = (.5, .5)
        # Rotate the bounding box
        angle = math.radians(angle)
        iw, ih = origin
        x1, y1, = self.bounding_box.p_min
        # Transforma as coordenadas para o sistema cartesiano
        y1 = ih - y1
        x1 -= iw
        # Calcula a posiçao dos pontos após a rotação
        x1_ = x1 * math.cos(angle) - y1 * math.sin(angle)
        y1_ = x1 * math.sin(angle) + y1 * math.cos(angle)
        # Transforma as coordenadas para o sistema da imagem
        y1_ = ih - y1_
        x1_ += iw
        # Atualiza os valores'
        sw, sh = self.width, self.height
        self.bounding_box.p_min = FloatPoint(x1_, y1_)
        self.bounding_box.p_max = FloatPoint(x1_ + sw, y1_ + sh)

    # Export functions
    def to_pixels(self) -> tuple[int]:
        xmin, ymin, xmax, ymax = self.bounding_box

        xmin = int(xmin * self.img_width)
        xmax = int(xmax * self.img_width)
        ymin = int(ymin * self.img_height)
        ymax = int(ymax * self.img_height)

        return xmin, ymin, xmax, ymax
    
    def to_json(self) -> dict:
        p_min, p_max = self.xyxy
        return {
            "class_id": self.class_name,
            "score": self.score,
            "bounding_box": [*p_min, *p_max],
        }
    
    def to_yolo(self) -> str:
        x, y, w, h = self.middle_point.x, self.middle_point.y, self.width, self.height
        return f"{self.class_id} {x} {y} {w} {h}"

    # Magic methods
    # sorted from top right to bottom left
    def __lt__(self, other):
        # Check if below entirely from the other
        vert_dist_from_other = self.middle_point.y - other.middle_point.y
        self_height = self.bounding_box.p_max.y - self.bounding_box.p_min.y
        # Magic number 0.9 is the coeficient to allow an minor sobreposition of detections
        # and still be considered below 
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
        return "{}_{:.2f}-{:.2f}-{:.2f}-{:.2f}".format(self.class_name, *[x for x in self.bounding_box])



## Label maps ##
@dataclass
class LabelMap:
    class Stage(Enum):
        FIRST = 0
        SECOND = 1
        
    detections : list[Detection.Type]
    stage : Stage

## Default Label Maps ##
DEFAULT_FIRST_STAGE_LABEL_MAP = LabelMap(
    detections = [
        Detection.Type.CPF_BLOCK,
        Detection.Type.QUESTION_BLOCK,
    ],
    stage = LabelMap.Stage.FIRST
)

DEFAULT_SECOND_STAGE_LABEL_MAP = LabelMap(
    detections = [
        Detection.Type.CPF_COLUMN,
        Detection.Type.QUESTION_LINE,
        Detection.Type.SELECTED_BALL,
        Detection.Type.UNSELECTED_BALL,
        Detection.Type.QUESTION_NUMBER,
        Detection.Type.QUESTION_COLUMN,
    ],
    stage = LabelMap.Stage.SECOND
)

        



