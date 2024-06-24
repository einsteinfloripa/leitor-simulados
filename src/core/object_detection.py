from __future__ import annotations

from utils.data_classes import FloatBoundingBox, FloatPoint


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
        self.aspect_ratio : float = (
            (self.bounding_box.ponto_max.y - self.bounding_box.ponto_min.y) /
            (self.bounding_box.ponto_max.x - self.bounding_box.ponto_min.x)  
        ) * (img_height / img_width)

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

    def to_json(self, for_annotation=False) -> dict:
        xmin, ymin, xmax, ymax = self.bounding_box
        if not for_annotation:
            return {
                "class_id": self.label_map[self.class_id],
                "score": self.score,
                "bounding_box": [xmin, ymin, xmax, ymax],
            }
        else:
            xmid, ymid = self.middle_point
            width, height = xmax - xmin, ymax - ymin
            return {
                "class_id": self.class_id,
                "score": self.score,
                "bbox": [xmid, ymid, width, height],
            }
        
    # sorted from top right to bottom left
    def __lt__(self, other):
        # check if below entirely from the other
        vert_dist_from_other = self.middle_point.y - other.middle_point.y
        self_height = self.bounding_box.ponto_max.y - self.bounding_box.ponto_min.y
        # magic number 0.9 is the coeficient to allow an minor sobreposition of detections
        # and still be considered below 
        if abs(vert_dist_from_other) > self_height * 0.9:
            if vert_dist_from_other < 0:
                return True
            else:
                return False
        
        # check if right entirely from the other
        hor_dist_from_other = self.middle_point.x - other.middle_point.x
        self_width = self.bounding_box.ponto_max.x - self.bounding_box.ponto_min.x
        # same magic number as above
        if abs(hor_dist_from_other) > self_width * 0.9:
            if hor_dist_from_other < 0:
                return True
            else:
                return False

        if vert_dist_from_other >= hor_dist_from_other:
            return self.middle_point.y < other.middle_point.y
        else:
            return self.middle_point.x < other.middle_point.x
    
    def __repr__(self) -> str:
        return "{}_{:.2f}-{:.2f}-{:.2f}-{:.2f}".format(self.class_name, *[x for x in self.bounding_box])




