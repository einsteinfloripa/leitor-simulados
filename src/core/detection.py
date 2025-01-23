from __future__ import annotations
import math

from utils.data_classes import FloatBoundingBox, FloatPoint, IntPoint, IntBoundingBox

class DetectionCoords():
    """
    A simpler representation of the detection, the coordenetes are all in relation
    to the root image

    Args:
        class_name (str): The class name of the detection
        bounding_box (IntBoundingBox): The bounding box of the detection
    """
    def __init__(self, class_name, int_bbox):
        self.class_name = class_name
        self.bbox : IntBoundingBox = int_bbox

    def __eq__(self, value):
        return self.bbox == value.bbox
    def __hash__(self):
        return hash((self.bbox, self.class_name))



class Detection:

    label_map = []

    def __init__(
            self,
            bounding_box,
            class_id,
            score,
            img_width,
            img_height,
            anchored_at = None
        ):
        self.bounding_box : FloatBoundingBox = bounding_box
        self.class_id : int = int(class_id)
        self.class_name : str = self.label_map[self.class_id]
        self.score : float = float(score)
        self.img_width : int =  img_width
        self.img_height : int = img_height
        self.anchored_at : IntPoint | None = anchored_at
    
    # Public Setters && getters
    @classmethod
    def set_label_map(cls, label_map):
        cls.label_map = label_map
    @classmethod
    def get_label_map(cls):
        return cls.label_map

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


    # Public functions
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

    def to_coords(self) -> DetectionCoords:
        # get the coordinate in pixels
        xmax = int(self.bounding_box.p_max.x * self.img_width)
        xmin = int(self.bounding_box.p_min.x * self.img_width)
        ymax = int(self.bounding_box.p_max.y * self.img_height)
        ymin = int(self.bounding_box.p_min.y * self.img_height)
        if self.anchored_at:
            xmin += self.anchored_at.x
            ymin += self.anchored_at.y
            xmax += self.anchored_at.x
            ymax += self.anchored_at.y
        int_bbox = IntBoundingBox.from_ints(xmin, ymin, xmax, ymax)
        return DetectionCoords(self.class_name, int_bbox)

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

