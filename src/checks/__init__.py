import aux.log as log

from aux.object_detection import Detection
from math import sqrt
from aux.image import Image
from aux.data_classes import FloatPoint, FloatBoundingBox
from typing import Callable


#File configs
__all__ = ['perform']

FILTER_DETECTIONS = None
FILTER_ONLY = None

logger = log.checks_logger


def load_checker(flag_prova : str):
    global _checker
    if flag_prova == 'PS':
        import checks.ps_alunos_checks as _checker
    elif flag_prova == 'SIMUFSC':
        raise NotImplementedError
    elif flag_prova == 'SIMUENEM':
        raise NotImplementedError
    else:
        raise ValueError(f'Prova inavlida: {flag_prova}')

# MAIN FUNCTION
def perform(img : Image, stage : int):


    logger.warning(f' ---- Performing checks on {img.name} ---- ')

    Checker.IMG_INSTANCE = img
    if FILTER_ONLY:
        _checker.setup_detections(img.detections, True, stage)
    else:
        _checker.setup_detections(img.detections, FILTER_DETECTIONS, stage)
        _checker.perform_checks(stage)

    logger.warning(f' --------- {img.name} PASSED --------- ')

#AUX CLASSES


'''
Sorry for this meta mess i didant find a cleaner way to do this 
The metaclass below is to ensure every Check child class gets
his own copy of the detections list and checks list
'''
# CHECKER CLASS
class Meta(type):
    def __init__(cls, name, bases, attrs):
        cls.detections = []
        cls.checks = {}
        cls.logger = log.get_new_logger(cls.__name__)
        super().__init__(name, bases, attrs)
    

class Checker(metaclass=Meta):
    
    IMG_INSTANCE : Image = None


    #public methods
    @classmethod
    def get_detections(cls) -> list[Detection]:
        return cls.detections
        
    # wrapper functions
    def has_detections(func) -> Callable:
        def wrapper(cls, *args, **kwargs):
            if len(cls.detections) == 0:
                cls.logger.info(f'No detections found!')
                return []
            else:
                return func(cls, *args, **kwargs)
        return wrapper
    
    def execute(func) -> Callable:
        def wrapper(cls, *args, **kwargs):
            try:
                result = func(cls, *args, **kwargs)
            except Exception as e:
                cls.logger.error(f'{"[ ERROR ]":10} {func.__name__} called with args {args} and kwargs {kwargs}')
                raise e
            if not result and not kwargs.get('filter', False):
                cls.logger.warning(f'{"[ FAIL ]":10} {func.__name__} called with args {args} and kwargs {kwargs}')
                raise AssertionError(f'{func.__name__} : FALIED', f'{cls.__name__}.{func.__name__} called with args {args} and kwargs {kwargs}')
            elif result:
                cls.logger.debug(f'[ PASSED ] {func.__name__} called with args {args} and kwargs {kwargs}')
            return result        
        return wrapper

    # checks
    @classmethod
    @execute
    def count(cls, expected_value : int, detections_type : str, **kwargs) -> bool:
        count = 0
        for detection in cls.detections:
            if detection.class_name == detections_type:
                count += 1
        cls.logger.debug(f'count : {count} == {expected_value}')
        return count == expected_value

    @classmethod
    @execute
    def center_is_near_of(
            cls, detection : Detection, point : FloatPoint, radius : float=None, **kwargs
        ) -> bool:
        # O raio é sempre em porcentagem da medida da altura da imagem
        radius = radius * cls.IMG_INSTANCE.height
        distance = cls._get_distance_between_points(detection.middle_point, point)
        return not distance > radius

    @classmethod
    @execute
    def horizontally_alling(cls, detections : list[Detection], tolerance = None, **kwargs) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_y : float = sum([point.y for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.y - average_y) > tolerance:
                return False
        return True

    @classmethod
    @execute
    def vertically_alling(cls, detections : list[Detection], tolerance = None, **kwargs) -> bool:
        points : list[FloatPoint] = [detection.middle_point for detection in detections]
        average_x = sum([point.x for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point.x - average_x) > tolerance:
                return False
        return True

    @classmethod
    @execute
    def contains(bigger : Detection, smaller : Detection, **kwargs):
        middle : FloatPoint = smaller.middle_point
        ymin, xmin, ymax, xmax = bigger.bounding_box
        result = ymin <= middle.y <= ymax and xmin <= middle.x <= xmax
        return result

    @classmethod
    @execute
    def aspect_ratio(
        cls, detection : Detection, expected_ratio : float, tolerance : float = None, **kwargs
        ) -> bool:
        return abs(detection.aspect_ratio - expected_ratio) <= tolerance

    @classmethod
    @execute
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
        while len(sorted_detections) > 0:
            group = []
            for _ in range(size):
                try:
                    group.append(sorted_detections.pop(0))
                except IndexError:
                    break
            groups.append(group)
    
        return groups
    