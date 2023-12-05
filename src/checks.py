import log

from math import sqrt
from object_detection import Detection
from image import Image
from data_classes import FloatPoint, FloatBoundingBox
from typing import Callable

#File configs
__all__ = ['perform']

logger = log.checks_logger

# MAIN FUNCTIONS
def perform(img : Image, filter_detections : bool = False, logfile : bool = False):
    if logfile: log.enable_file_logging()

    Checker.IMG_INSTANCE = img
    setup_detections(img.detections, filter_detections)
    
    return get_report()


def setup_detections(detections : list[Detection], filter_detections : bool) -> None:
        CHECKERS_MAP = {'cpf_block':CpfBlockChecker, 'questions_block':QuestionsBlockChecker,
            'cpf_column':CpfColumnChecker, 'question_line':QuestionLineChecker,
            'selected_ball':SelectedBallChecker, 'unselected_ball':UnselectedBallChecker,
            'question_number':QuestionNumberChecker
        }
        logger.debug(f'Setup for detections')
        # clear old detections and checks values
        for check_class in CHECKERS_MAP.values():
            check_class.detections.clear()
            check_class.checks.clear()

        # dispatch detections to their respective checkers
        if detections:
            for detection in detections:
                handler_class = CHECKERS_MAP[detection.class_name]
                handler_class.detections.append(detection)
        
        # call auxiliar variables constructor for each class
        for cls in CHECKERS_MAP.values():
            if hasattr(cls, '_precheck_setup'):
                cls._precheck_setup()

        # clean detections
        if filter_detections:
            for cls in CHECKERS_MAP.values():
                cls.clean_detections()


def get_report() -> dict[str, str]:
    return {
        # "selected_ball" : SelectedBallChecker.perform_checks(),
        # "unselected_ball" : UnselectedBallChecker.perform_checks(),
        # "cpf_column" : CpfColumnChecker.perform_checks(),
        "cpf_block" : CpfBlockChecker.perform_checks(),
        "question_block" : QuestionsBlockChecker.perform_checks(),
        # "question_line" : QuestionLineChecker.perform_checks(),
        # "question_number" : QuestionNumberChecker.perform_checks()
    }


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
# CHECKER CLASSES
class Meta(type):
    def __init__(cls, name, bases, attrs):
        cls.detections = []
        cls.checks = {}
        super().__init__(name, bases, attrs)
    

class Checker(metaclass=Meta):

    IMG_INSTANCE : Image = None

    def has_detections(func) -> Callable:
        def wrapper(cls, *args, **kwargs):
            if len(cls.detections) == 0:
                logger.warning(f'No detections found for [{cls.__name__}]')
                return []
            else:
                return func(cls, *args, **kwargs)
        return wrapper
    
    def log_result(func) -> Callable:
        def wrapper(cls, *args, **kwargs):
            result = func(cls, *args, **kwargs)
            if not result:
                logger.warning(f'[{kwargs["name"]}] : FALIED')
                logger.warning(f'{cls.__name__}.{func.__name__} called with args {args} and kwargs {kwargs}')
            else:
                logger.debug(f'[{kwargs["name"]}] : PASSED')
                logger.debug(f'{cls.__name__}.{func.__name__} called with args {args} and kwargs {kwargs}')
            return result        
        return wrapper

    # checks
    @classmethod
    @log_result
    def count(cls, expected_value : int, detections_type : str, **kwargs) -> bool:
        count = 0
        for detection in cls.detections:
            if detection.class_name == detections_type:
                count += 1
        return count == expected_value

    @classmethod
    @log_result
    def center_is_near_of(
            cls, detection : Detection, point : FloatPoint, radius : float=0.05, **kwargs
        ) -> bool:
        distance = cls._get_distance_between_points(detection.middle_point, point)
        return not distance > radius

    @classmethod
    @log_result
    def horizontally_alling(cls, detections : list[Detection], tolerance = 0.05, **kwargs) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_y : float = sum([point.y for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.y - average_y) > tolerance:
                return False
        return True

    @classmethod
    @log_result
    def vertically_alling(cls, detections : list[Detection], tolerance = 0.05, **kwargs) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_x = sum([point.x for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.x - average_x) > tolerance:
                return False
        return True

    @classmethod
    @log_result
    def contains(bigger : Detection, smaller : Detection, **kwargs):
        middle : FloatPoint = smaller.middle_point
        ymin, xmin, ymax, xmax = bigger.bounding_box
        result = ymin <= middle.y <= ymax and xmin <= middle.x <= xmax
        return result

    @classmethod
    @log_result
    def aspect_ratio(
        cls, detection : Detection, expected_ratio : float, tolerance : float = 0.1, **kwargs
        ) -> bool:
        width, height = cls._get_width_and_height(detection)
        aspect_ratio = width / height
        return abs(aspect_ratio - expected_ratio) <= tolerance

    @classmethod
    @log_result
    def inside_box(cls, detection : Detection, bound_box : FloatBoundingBox, **kwargs) -> bool:
        point = detection.middle_point
        result = (bound_box.ponto_min.x <= point.x <= bound_box.ponto_max.x 
                  and bound_box.ponto_min.y <= point.y <= bound_box.ponto_max.y)
        return result


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
    def _get_width_and_height(cls, detection : Detection) -> tuple[float, float]:
        xmin, ymin, xmax, ymax = detection.to_pixels()
        return (xmax - xmin, ymax - ymin)

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


################# FIRST STAGE CHECKS #####################
class CpfBlockChecker(Checker):
    EXPECTED_COUNT =           1
    EXPECTED_COLUMN_COUNT =   11
    EXPECTED_ASPECT_RATIO = 0.5847
    EXPECTED_AVERAGE_MIDDLE_POINT : FloatPoint = FloatPoint(0.3443, 0.3013)


    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'[{__class__.__name__}] Cleaning detections...')
        to_remove = []
        for detection in cls.detections:
            # Position
            if not cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1):
                to_remove.append(detection)
                logger.warning(f'[{__class__.__name__}] : Deleting out of bound detection : {detection}')
                continue
            # Aspect Ratio
            elif not cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1):
                to_remove.append(detection)
                logger.warning(f'[{__class__.__name__}] : Deleting bad aspect ratio detection : {detection}')
                continue

        for detection in to_remove:
            cls.detections.remove(detection)

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):
        logger.debug(f'[{__class__.__name__}] Performing checks on...')
        flag_ok = True

        checks = [ 
            cls.count(cls.EXPECTED_COUNT, 'cpf_block', name='cpf_block_count')
        ]
        for detection in cls.detections:
            checks.append(cls.center_is_near_of(detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT, name="cpf_block_center_is_near_of"))
        for detection in cls.detections:
            checks.append(cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1, name="cpf_block_aspect_ratio"))

        return False in checks


class QuestionsBlockChecker(Checker):
    EXPECTED_QUESTIONS_BLOCK_COUNT = 6
    EXPECTED_AVERAGE_MIDDLE_POINTS = [
        FloatPoint(0.2101, 0.5249), FloatPoint(0.5, 0.5249), FloatPoint(0.7713, 0.5249),
        FloatPoint(0.2101, 0.7245), FloatPoint(0.5, 0.7245), FloatPoint(0.7713, 0.7245)
    ]
    EXPECTED_ASPECT_RATIO =  1.1896
    UPPER_TREE_BLOCKS : list[Detection] = []
    LOWER_TREE_BLOCKS : list[Detection] = []
    NAMES = ['upper_left', 'upper_middle', 'upper_right', 'lower_left', 'lower_middle', 'lower_right']

    
    @classmethod
    def _precheck_setup(cls):
        sorted = cls._sort_vertically(cls.detections)
        top_tree = sorted[:3]
        lower_tree = sorted[3:]

        cls.UPPER_TREE_BLOCKS = cls._sort_horizontally(top_tree)
        cls.LOWER_TREE_BLOCKS = cls._sort_horizontally(lower_tree)
        cls.sorted_detections = cls.UPPER_TREE_BLOCKS + cls.LOWER_TREE_BLOCKS

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'[{__class__.__name__}] Cleaning detections...')
        to_remove = []
        for detection in cls.detections:
            # Position
            if not cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1):
                to_remove.append(detection)
                logger.warning(f'[{__class__.__name__}] Deleting out of bound detection :  {detection}')
                continue
            # Aspect Ratio
            elif not cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1):
                to_remove.append(detection)
                logger.warning(f'[{__class__.__name__}] Deleting bad aspect ratio detection : {detection}')
                continue

        for detection in to_remove:
            cls.detections.remove(detection)


    @classmethod
    @Checker.has_detections
    def perform_checks(cls):
        logger.debug(f'[{__class__.__name__}] Performing checks...')

        checks = [ c for c in [
                cls.count(cls.EXPECTED_QUESTIONS_BLOCK_COUNT, 'questions_block', name="question_block_count"),
                cls.horizontally_alling(cls.UPPER_TREE_BLOCKS, tolerance=0.01, name="upper_tree_blocks_aling_horizontally"),
                cls.horizontally_alling(cls.LOWER_TREE_BLOCKS, tolerance=0.01, name="lower_tree_blocks_aling_horizontally"),
                cls.vertically_alling([cls.UPPER_TREE_BLOCKS[0], cls.LOWER_TREE_BLOCKS[0]], tolerance=0.01, name="left_most_blocks_aling_vertically"),
                cls.vertically_alling([cls.UPPER_TREE_BLOCKS[1], cls.LOWER_TREE_BLOCKS[1]], tolerance=0.01, name="midle_blocks_aling_vertically"),
                cls.vertically_alling([cls.UPPER_TREE_BLOCKS[2], cls.LOWER_TREE_BLOCKS[2]], tolerance=0.01, name="right_most_blocks_align_vertically"),
            ]]
        for point, detection, name in zip(cls.EXPECTED_AVERAGE_MIDDLE_POINTS, cls.sorted_detections, cls.NAMES):
            checks.append(cls.center_is_near_of(detection, point, name=f"{name}_question_block_center_is_near_of"))
        for detection in cls.detections:
            checks.append(cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1, name="question_block_aspect_ratio"))
        
        return False in checks



################# SECOND STAGE CHECKS #####################
class CpfColumnChecker(Checker):
    
    def perform_checks():
        return []
        if len(cls.detections) == 0:
            return None
        return cls.checks


    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'Cleaning {__class__} detections...')
        to_remove = []
        for detection in cls.sorted_detections:
            if not cls.center_is_near_of(detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT, radius=0.2):
                to_remove.append(detection)
        
        for detection in to_remove:
            logger.warning(f'Deleting {detection} from image')
            cls.detections.remove(detection)


class QuestionLineChecker(Checker):
    EXPECTED_QUESTION_LINE_COUNT = 10
    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.4, y_min=0.17, x_max=0.6, y_max=0.96
    )

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'Cleaning {__class__} detections...')
        to_remove = []
        for detection in cls.detections:
            if not cls.inside_box(detection, cls.EXPECTED_INTERVAL):
                to_remove.append(detection)

        for detection in to_remove:
            logger.warning(f'Deleting {detection} from image')
            cls.detections.remove(detection)


    @classmethod
    @Checker.has_detections
    def perform_checks(cls):
        
        cls.checks.append( {"question_line_count":cls.count(cls.EXPECTED_QUESTION_LINE_COUNT, 'question_line')} )
        cls.checks.append( {"question_line_vertically_aling":cls.vertically_alling(cls.detections, tolerance=0.05)} )

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
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'Cleaning {__class__} detections...')
        to_remove = []
        for detection in cls.detections:
            if not cls.inside_box(detection, cls.EXPECTED_INTERVAL):
                to_remove.append(detection)

        for detection in to_remove:
            logger.debug(f'Deleting {detection} from image')
            cls.detections.remove(detection)
        logger.debug(f'Successfully cleaned {__class__} detections')



    @classmethod
    @Checker.has_detections
    def perform_checks(cls):
        
        cls.checks.append( {"question_number_count":cls.count(cls.EXPECTED_QUESTION_NUMBER_COUNT, 'question_number')} )
        cls.checks.append( {"question_number_vertically_aling":cls.vertically_alling(cls.detections, tolerance=0.05)} )

        return cls.checks


class SelectedBallChecker(Checker):
    EXPECTED_INTERVAL = FloatBoundingBox.from_floats(
        x_min=0.138, y_min=0.17, x_max=0.96, y_max=0.96
)
    EXPECTED_SELECTED_BALL_COUNT = 10
    

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        logger.debug(f'Cleaning {__class__} detections...')
        to_remove = []
        for detection in cls.detections:
            if not cls.inside_box(detection, cls.EXPECTED_INTERVAL):
                to_remove.append(detection)

        for detection in to_remove:
            logger.Info(f'Deleting {detection} from image')
            cls.detections.remove(detection)


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



