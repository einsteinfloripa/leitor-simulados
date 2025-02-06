from __future__ import annotations

import utils.log as log

from core.detection.base import Detection
from math import sqrt
from core.image import Image
from utils.data_classes import FloatPoint, FloatBoundingBox
from typing import Callable


#File configs
FILTER_DETECTIONS = None
CONTINUE_ON_FAIL = None
SAVE_YOLO = False

logger = log.checks_logger


def load_checker(flag_prova : str):
    class EmptyChecker:
        __EMPTYCHECKER__ = True
    global _checker
    flag_prova = flag_prova.upper()
    if flag_prova == 'PS':
        import checks.ps_alunos_checks as _checker
    elif flag_prova == 'SIMUFSC':
        _checker = EmptyChecker
    elif flag_prova == 'SIMUENEM':
        _checker = EmptyChecker
    elif flag_prova == 'PS':
        _checker = EmptyChecker
    elif flag_prova == 'SIMULINHO':
        _checker = EmptyChecker
    else:
        raise ValueError(f'Prova inavlida: {flag_prova}')

# MAIN FUNCTION
def perform(img : Image, stage : int):

    if not img.detections:
        logger.error(f' ---- No detections found on {img.name} ---- ')
        return 'failed'
    if hasattr(_checker, '__EMPTYCHECKER__'):
        logger.error(f' ---- No checks performed on {img.name} ---- ')
        return 'suceess'

    logger.error(f' ---- Performing checks on {img.name} ---- ')

    Checker.IMG_INSTANCE = img
    
    try:
        _checker.setup_detections(img.detections, FILTER_DETECTIONS, stage)
        _checker.perform_checks(stage)
    except AssertionError:
        logger.error(f' --------- {img.name} FAILED --------- ')
        if not CONTINUE_ON_FAIL:
            raise
        return 'failed'

    logger.error(f' --------- {img.name} PASSED --------- ')
    return 'success'


'''
Sorry for this meta mess i didant find a cleaner way to do this 
The metaclass below is to ensure every Check child class gets
his own copy of the detections list and checks list
this is done so that fewer objects are created and destroyed
'''
# CHECKER CLASS
class Meta(type):
    def __init__(cls, name, bases, attrs):
        cls.detections = []
        cls.logger = log.get_new_logger(cls.__name__)
        cls.fail = False
        super().__init__(name, bases, attrs)
    

class Checker(metaclass=Meta):
    
    IMG_INSTANCE : Image = None

    # Public getters
    @classmethod
    def get_detections(cls) -> list[Detection]:
        return cls.detections
    
    # Wrapper functions
    def has_detections(func) -> Callable:
        '''Ensures that the function is only called if there are detections to be checked'''
        def wrapper(cls, *args, **kwargs):
            if len(cls.detections) == 0:
                if hasattr(cls, 'EXPECTED_COUNT'):
                    cls.logger.warning(f'[ FALIED ] No detections found! Expected {cls.EXPECTED_COUNT} detections')
                    raise AssertionError(f'No detections found! Expected {cls.EXPECTED_COUNT} detections')
                cls.logger.info(f'No detections found!')
                return []
            else:
                return func(cls, *args, **kwargs)
        return wrapper
    
    def execute(func) -> Callable:
        '''Executes the test function and logs the result'''
        def wrapper(cls, *args, **kwargs):
            try:
                func(cls, *args, **kwargs)
                cls.logger.debug(f'[ PASSED ] {func.__name__} {args} {kwargs}')
            except AssertionError as e:
                if kwargs.get('filter', False):
                    cls.logger.info(f'[ REMOVED DETECTION ] {func.__name__}: {e}')
                    cls.logger.debug(f'Delecting detections: {e.args[1]}')
                    cls.reproved.extend(e.args[1])
                else:
                    cls.logger.error(f'[ FALIED ] {func.__name__}: {e}')
                    cls.fail = True
                    if not CONTINUE_ON_FAIL:
                        raise e

            except Exception as e:
                raise e

        return wrapper
    
    # Auxiliar functions
    @classmethod
    def flush_reproved(cls):
        for detection in cls.reproved:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                cls.logger.error(f'Cant remove detection {detection} from detections')
                continue
        cls.reproved.clear()

    # Check functions
    @classmethod
    @execute
    def count(cls, expected_value : int, detections_type : str, **kwargs) -> bool:
        count = 0
        for detection in cls.detections:
            if detection.class_name == detections_type:
                count += 1
        
        if not count == expected_value:
            raise AssertionError( 
                f'count == {expected_value}  ::  {count} == {expected_value}'
            )

    @classmethod
    @execute
    def center_is_near_of(
            cls, detection : Detection, target : FloatPoint, radius : float=None, **kwargs
        ) -> bool:
        # By convention the radius is always a percentage of the image HEIGHT
        radius = radius * cls.IMG_INSTANCE.height
        distance = cls._get_distance_between_points(detection.middle_point, target)
        if not distance <= radius:
            raise AssertionError(
                f'distance <= radius  ::  {distance:.4f} <= {radius:.4f}',
                [detection]
            )
        
    @classmethod
    @execute
    def horizontally_alling(cls, detections : list[Detection], tolerance = None, **kwargs) -> bool:
        average_y : float = sum([detection.middle_point.y for detection in detections]) / len(detections)
        bad_detections = []
        for detection in detections:
            if abs(detection.middle_point.y - average_y) > tolerance:
                bad_detections.append(detection)
        if bad_detections:
            string = ' | '.join([f'{abs(detection.middle_point.y - average_y):.4f} < {tolerance:.4f}' for detection in bad_detections])
            raise AssertionError(
                f'abs(detection.middle_point.y - average_y) <= tolerance  ::  {string}',
                bad_detections
            )

    @classmethod
    @execute
    def vertically_alling(cls, detections : list[Detection], tolerance = None, **kwargs) -> bool:
        average_x : float = sum([detection.middle_point.x for detection in detections]) / len(detections)
        bad_detections = []
        for detection in detections:
            if abs(detection.middle_point.x - average_x) > tolerance:
                bad_detections.append(detection)
        if bad_detections:
            string = ' | '.join([f'{abs(detection.middle_point.x - average_x):.4f} <= {tolerance:.4f}' for detection in bad_detections])
            raise AssertionError(
                f'abs(detection.middle_point.x - average_x) < tolerance  ::  {string}',
                bad_detections
            )

    @classmethod
    @execute
    def contains(bigger : Detection, smaller : Detection, **kwargs):
        middle : FloatPoint = smaller.middle_point
        ymin, xmin, ymax, xmax = bigger.bounding_box
        result = ymin <= middle.y <= ymax and xmin <= middle.x <= xmax
        if not result:
            raise AssertionError(
                f'b.ymin <= s.y <= b.ymax and b.xmin <= s.x <= b.xmax  ::  {ymin:.4f} <= {middle.y:.4f} <= {ymax:.4f} and {xmin:.4f} <= {middle.x:.4f} <= {xmax:.4f}',
                [bigger, smaller]
            )

    @classmethod
    @execute
    def aspect_ratio(
        cls, detection : Detection, expected_ratio : float, tolerance : float = None, **kwargs
        ) -> bool:
        if not abs(detection.aspect_ratio - expected_ratio)/expected_ratio <= tolerance:
            raise AssertionError(
                f'abs(detection.aspect_ratio - expected_ratio) <= tolerance  ::  {abs((detection.aspect_ratio - expected_ratio)/expected_ratio):.4f} <= {tolerance}',
                [detection]
            )

    @classmethod
    @execute
    def inside_box(cls, detection : Detection, bound_box : FloatBoundingBox, **kwargs) -> bool:
        point = detection.middle_point
        result = (bound_box.p_min.x <= point.x <= bound_box.p_max.x 
                  and bound_box.p_min.y <= point.y <= bound_box.p_max.y)
        if not result:
            raise AssertionError(
                f'min.x <= detection.x <= max.x and min.y <= detection.y <= max.y  ::  {bound_box.p_min.x:.4f} <= {point.x:.4f} <= {bound_box.p_max.x:.4f} and {bound_box.p_min.y:.4f} <= {point.y:.4f} <= {bound_box.p_max.y:.4f}',
                [detection]
            )


    # Below methods are tools and cannot be used as checks

    @classmethod
    def _get_distance_between_points(
            cls,
            point1 : FloatPoint, point2 : FloatPoint
        ) -> float:
        point1, point2 = cls._transform([point1, point2])
        return sqrt(
            (point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2
        )
    # recupera o dominio inicial
    @classmethod
    def _transform(cls, points) -> list[FloatPoint]:
        return [FloatPoint(x * cls.IMG_INSTANCE.width , y * cls.IMG_INSTANCE.height) for x, y in points]
    
    @classmethod
    def _sort_vertically(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point.y)

    @classmethod
    def _sort_horizontally(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point.x)

    @classmethod
    def _group_by_axis(cls, detections : list[Detection], size, axis=None) -> list[list[Detection]]:
        if axis == 'x':
            sorted_detections = cls._sort_horizontally(detections)
        elif axis == 'y':
            sorted_detections = cls._sort_vertically(detections)
        else:
            raise ValueError("axis must be 'x' or 'y'")
        
        groups = []
        while len(sorted_detections) > size:
            group = []
            for _ in range(size):
                group.append(sorted_detections.pop(0))

            groups.append(group)
            
        if sorted_detections:
            groups.append(sorted_detections)

        return groups
    