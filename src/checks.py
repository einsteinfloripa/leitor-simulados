from math import sqrt
from object_detection import Detection
from image import Image
from data_classes import FloatPoint, FloatBoundingBox

__all__ = ['perform']



def perform(img : Image):
    clear_checks()
    Checker.IMG_INSTANCE = img
    dispatch_detections(img.detections)
    return get_report()
    
def clear_checks():
    CHECKERS_MAP = {'cpf_block':CpfBlockChecker, 'questions_block':QuestionsBlockChecker,
            'cpf_column':CpfColumnChecker, 'question_line':QuestionLineChecker,
            'selected_ball':SelectedBallChecker, 'unselected_ball':UnselectedBallChecker,
            'question_number':QuestionNumberChecker
        }
    for check_class in CHECKERS_MAP.values():
        check_class.detections.clear()
        check_class.checks.clear()

def dispatch_detections(detections : list[Detection]) -> None:
        
        CHECKERS_MAP = {'cpf_block':CpfBlockChecker, 'questions_block':QuestionsBlockChecker,
            'cpf_column':CpfColumnChecker, 'question_line':QuestionLineChecker,
            'selected_ball':SelectedBallChecker, 'unselected_ball':UnselectedBallChecker,
            'question_number':QuestionNumberChecker
        }

        for detection in detections:
            handler_class = CHECKERS_MAP[detection.class_name]
            handler_class.detections.append(detection)
        

def get_report():
    

    report =  {
        "selected_ball" : SelectedBallChecker.perform_checks(),
        "unselected_ball" : UnselectedBallChecker.perform_checks(),
        "cpf_column" : CpfColumnChecker.perform_checks(),
        "cpf_block" : CpfBlockChecker.perform_checks(),
        "question_block" : QuestionsBlockChecker.perform_checks(),
        "question_line" : QuestionLineChecker.perform_checks(),
        "question_number" : QuestionNumberChecker.perform_checks()

    }
    return report


#AUX CLASSES
def Group():
    
    def __init__(self, detections : list[Detection]) -> None:
        self.detections = detections
        self.middle_point = self._get_middle_point()

    def add(self, detection : list[Detection]) -> None:
        self.detections.append(detection)
        self.middle_point = self._get_middle_point()

    def _get_middle_point(self) -> tuple[float, float]:
        x = sum([detection.middle_point[0] for detection in self.detections]) / len(self.detections)
        y = sum([detection.middle_point[1] for detection in self.detections]) / len(self.detections)
        return (x, y)


'''
Sorry for this meta mess i didant find a cleaner way to do this 
The metaclass below is to ensure every Check child class gets
his own copy of the detections list and checks list
'''
class Meta(type):
    def __init__(cls, name, bases, attrs):
        cls.detections = []
        cls.checks = []
        super().__init__(name, bases, attrs)

class Checker(metaclass=Meta):

    IMG_INSTANCE : Image = None

    # checks

    @classmethod
    def count(cls, expected_value : int, detections_type : str) -> bool:
        count = 0
        for detection in cls.detections:
            if detection.class_name == detections_type:
                count += 1
        if count != expected_value:
            return f'FAIL: Expected {expected_value} {detections_type} detections, got {count}'
        return "PASSED" 

    @classmethod
    def center_is_near_of(
            cls, detection : Detection, point : FloatPoint, radius : float=0.05
        ) -> bool:
        distance = cls._get_distance_between_points(detection.middle_point, point)
        if distance > radius:
            return f'FAIL: Expected {detection.class_name} center to be near of {point}, got {detection.middle_point}'
        return "PASSED"

    @classmethod
    def horizontally_alling(cls, detections : list[Detection], tolerance = 0.05) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_y : float = sum([point.y for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.y - average_y) > tolerance:
                return f'FAIL: Expected {detections[0].class_name} to be horizontally alligned, got points: {points}'
        return "PASSED"

    @classmethod
    def vertically_alling(cls, detections : list[Detection], tolerance = 0.05) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_x = sum([point.x for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.x - average_x) > tolerance:
                return f'FAIL: Expected {detections[0].class_name} to be vertically alligned, got points: {points}'
        return "PASSED"

    @classmethod
    def contains(bigger : Detection, smaller : Detection):
        middle : FloatPoint = smaller.middle_point
        ymin, xmin, ymax, xmax = bigger.bounding_box
        result = ymin <= middle.y <= ymax and xmin <= middle.x <= xmax
        if not result:
            return f'FAIL: Expected {smaller.class_name} to be inside {bigger.class_name}, got {smaller.middle_point}'
        return "PASSED"


    @classmethod
    def aspect_ratio(cls, detection : Detection, expected_ratio : float, tolerance : float = 0.1) -> bool:
        aspect_ratio = detection.width / detection.height
        if not abs(aspect_ratio - expected_ratio) <= tolerance:
            return f'FAIL: Expected {detection.class_name} aspect ratio to be {expected_ratio}, got {aspect_ratio}'
        return "PASSED"


    @classmethod
    def inside_box(cls, detection : Detection, bound_box : FloatBoundingBox) -> bool:
        point = detection.middle_point
        result = (bound_box.ponto_min.x <= point.x <= bound_box.ponto_max.x 
                  and bound_box.ponto_min.y <= point.y <= bound_box.ponto_max.y)
        if not result:
            return f'FAIL: Expected {detection.class_name} to be inside {bound_box}, got {detection.middle_point}'
        return "PASSED"


    # Below methods are tools and cannot be used as checks

    @classmethod
    def _get_distance_between_points(
            cls,
            point1 : FloatPoint, point2 : FloatPoint
        ) -> float:
        return sqrt(
            (point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2
        )
    
    @classmethod
    def _sort_vertically(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point.y)

    @classmethod
    def _sort_horizontally(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point.x)

    @classmethod
    def _group_by(cls, detections : list[Detection], axis=None, spacing=0.03) -> list[list[Detection]]:
        if axis == 'x':
            sorted_detections = cls._sort_horizontally(detections)
            p_index = 0
        elif axis == 'y':
            sorted_detections = cls._sort_vertically(detections)
            p_index = 1
        else:
            raise ValueError("axis must be 'x' or 'y'")
        
        groups = []
        for n, elem in enumerate(sorted_detections):
            if n == 0:
                group = Group([elem])
                continue
            if abs(elem.middle_point[p_index] - group[-1].middle_point[p_index]) <= spacing:
                group.append(elem)
            else:
                groups.append(group)
                group = Group([elem])
        
        return groups


# First stage
class CpfBlockChecker(Checker):
    EXPECTED_COUNT =         1
    EXPECTED_COLUMN_COUNT = 11
    EXPECTED_AVERAGE_MIDDLE_POINT : FloatPoint = FloatPoint(0.3443, 0.3013)

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        cls.checks.append( {"cpf_block_count":cls.count(cls.EXPECTED_COUNT, 'cpf_block')} )
        cpf_block_detection = cls.detections[0]
        cls.checks.append( {"cpf_column_count":cls.count(cls.EXPECTED_COLUMN_COUNT, 'cpf_column')} )
        cls.checks.append( {"cpf_block_center_is_near_of":cls.center_is_near_of(cpf_block_detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT)} )

        return cls.checks

class QuestionsBlockChecker(Checker):
    EXPECTED_QUESTIONS_BLOCK_COUNT = 6
    EXPECTED_AVERAGE_MIDDLE_POINTS = [
        FloatPoint(0.2101, 0.5249), FloatPoint(0.5, 0.5249), FloatPoint(0.7713, 0.5249),
        FloatPoint(0.2101, 0.7245), FloatPoint(0.5, 0.7245), FloatPoint(0.7713, 0.7245)
    ]
    UPPER_TREE_BLOCKS : list[Detection] = []
    LOWER_TREE_BLOCKS : list[Detection] = []
    NAMES = ['upper_left', 'upper_middle', 'upper_right', 'lower_left', 'lower_middle', 'lower_right']

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        cls._sort_top_left_to_bottom_right(cls.detections)
        sorted_detections = cls.UPPER_TREE_BLOCKS + cls.LOWER_TREE_BLOCKS
        cls.checks.append( {"question_block_count":cls.count(cls.EXPECTED_QUESTIONS_BLOCK_COUNT, 'questions_block')} )
        cls.checks.append( {"upper_tree_blocks_aling_horizontally":cls.horizontally_alling(cls.UPPER_TREE_BLOCKS, tolerance=0.01)} )
        cls.checks.append( {"lower_tree_blocks_aling_horizontally":cls.horizontally_alling(cls.LOWER_TREE_BLOCKS, tolerance=0.01)} )
        cls.checks.append( {"left_most_blocks_aling_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[0], cls.LOWER_TREE_BLOCKS[0]], tolerance=0.01)} )
        cls.checks.append( {"midle_blocks_aling_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[1], cls.LOWER_TREE_BLOCKS[1]], tolerance=0.01)} )
        cls.checks.append( {"right_most_blocks_align_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[2], cls.LOWER_TREE_BLOCKS[2]], tolerance=0.01)} )
        for point, detection, name in zip(cls.EXPECTED_AVERAGE_MIDDLE_POINTS, sorted_detections, cls.NAMES):
            cls.checks.append( {f"{name}_question_block_center_is_near_of":cls.center_is_near_of(detection, point)} )

        return cls.checks
                
    @classmethod
    def _sort_top_left_to_bottom_right(cls, detections : list[Detection]) -> list[Detection]:
        sorted = cls._sort_vertically(detections)
        top_tree = sorted[:3]
        lower_tree = sorted[3:]
        cls.UPPER_TREE_BLOCKS = cls._sort_horizontally(top_tree)
        cls.LOWER_TREE_BLOCKS = cls._sort_horizontally(lower_tree)


# Second stage
class CpfColumnChecker(Checker):
    
    def perform_checks():
        return []
        if len(cls.detections) == 0:
            return None
        return cls.checks

class QuestionLineChecker(Checker):
    EXPECTED_QUESTION_LINE_COUNT = 10
    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.4, y_min=0.17, x_max=0.6, y_max=0.96
    )

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        to_remove = []
        for detection in cls.detections:
            result = cls.inside_box(detection, cls.EXPECTED_INTERVAL)
            if "FAIL" in result:
                result = "DELETING DETECTION FROM LIST\n ->" + result
                to_remove.append(detection)
            cls.checks.append( {f"{detection}_inside_expected_interval":result })

        cls.checks.append( {"question_line_count":cls.count(cls.EXPECTED_QUESTION_LINE_COUNT, 'question_line')} )
        cls.checks.append( {"question_line_vertically_aling":cls.vertically_alling(cls.detections, tolerance=0.05)} )

        for detection in to_remove:
            cls.IMG_INSTANCE.detections.remove(detection)

        return cls.checks


    @classmethod
    def get_vertically_sorted(cls) -> list[Detection]:
        return cls._sort_vertically(cls.detections)


class QuestionNumberChecker(Checker):

    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.09, y_min=0.17, x_max=0.15, y_max=0.96
    )
    EXPECTED_QUESTION_NUMBER_COUNT = 10

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        to_remove = []
        for detection in cls.detections:
            result = cls.inside_box(detection, cls.EXPECTED_INTERVAL)
            if "FAIL" in result:
                result = "DELETING DETECTION FROM LIST\n ->" + result
                to_remove.append(detection)
            cls.checks.append( {f"{detection}_inside_expected_interval":result })
        for element in to_remove:
            cls.IMG_INSTANCE.detections.remove(element)

        cls.checks.append( {"question_number_count":cls.count(cls.EXPECTED_QUESTION_NUMBER_COUNT, 'question_number')} )
        cls.checks.append( {"question_number_vertically_aling":cls.vertically_alling(cls.detections, tolerance=0.05)} )

        return cls.checks


class SelectedBallChecker(Checker):
    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.138, y_min=0.17, x_max=0.96, y_max=0.96
)
    EXPECTED_SELECTED_BALL_COUNT = 10
    
    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        to_remove = []
        for detection in cls.detections:
            result = cls.inside_box(detection, cls.EXPECTED_INTERVAL)
            if "FAIL" in result:
                result = "DELETING DETECTION FROM LIST\n ->" + result
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            cls.checks.append( {f"{detection}_inside_expected_interval":result })
        for element in to_remove:
            cls.IMG_INSTANCE.detections.remove(element)

        cls.checks.append( {"selected_ball_count":cls.count(cls.EXPECTED_SELECTED_BALL_COUNT, 'selected_ball')} )
        
        return cls.checks

class UnselectedBallChecker(Checker):
    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.138, y_min=0.17, x_max=0.96, y_max=0.96
    )
    EXPECTED_UNSELECTED_BALL_COUNT = 40
    
    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []

        to_remove = []
        for detection in cls.detections:
            result = cls.inside_box(detection, cls.EXPECTED_INTERVAL)
            if "FAIL" in result:
                result = "DELETING DETECTION FROM LIST\n ->" + result
                to_remove.append(detection) 
            cls.checks.append( {f"{detection}_inside_expected_interval":result })
        for element in to_remove:
            cls.IMG_INSTANCE.detections.remove(element)

        cls.checks.append( {"unselected_ball_count":cls.count(cls.EXPECTED_UNSELECTED_BALL_COUNT, 'unselected_ball')} )
        
        return cls.checks
    
    @classmethod
    def get_y_grouped(cls):
        return cls._group_by(cls.detections, axis='y', spacing=0.05)


class QuestionLineClusterChecker(Checker):
    EXPECTED_SELECTED_BALL_COUNT =  1
    EXPECTED_UNSELECTED_BALL_COUNT =  4
    EXPECTED_QUESTION_NUMBER_COUNT = 1
    
    question_line_vsorted = QuestionLineChecker.get_vertically_sorted()
    selected_balls_grouped = UnselectedBallChecker.get_y_grouped()



