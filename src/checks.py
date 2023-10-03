from math import sqrt

from object_detection import Detection


def dispatch_detections(detections : list[Detection], stage : int = 1) -> None:
        MAP_STAGE_1 = {'cpf_block':CpfBlockChecker, 'questions_block':QuestionsBlockChecker}
        MAP_STAGE_2 = {
            'cpf_column':CpfColumnChecker, 'question_line':QuestionLineChecker,
            'selected_ball':SelectedBallChecker, 'unselected_ball':UnselectedBallChecker,
            'question_number':QuestionNumberChecker
        }
        
        if stage == 1:
            for detection in detections:
                handler_class = MAP_STAGE_1[detection.class_name]
                handler_class.detections.append(detection)
                
                # print(f'{handler_class.__name__} detection: {detection.class_name}')
        
        elif stage == 2:
            for detection in detections:
                handler_class = MAP_STAGE_2[detection.class_name]
                handler_class.detections.append(detection)
                
                # print(f'{handler_class.__name__} detection: {detection.class_name}')

def get_report():
    report = {
        "cpf_block" : CpfBlockChecker.perform_checks(),
        "question_block" : QuestionsBlockChecker.perform_checks()
    }
    return report    


'''
Sorry for this meta mess i didant find a cleaner way to do this 
(I didant wanted to instanciate any objects)
The metaclass below is to ensure every Check child class gets
his own copy of the detections list and checks list
'''
class Meta(type):
    def __init__(cls, name, bases, attrs):
        cls.detections = []
        cls.checks = []
        super().__init__(name, bases, attrs)

class Checker(metaclass=Meta):

    # checks

    @classmethod
    def count(cls, expected_value : int, detections_type : str) -> bool:
        count = 0
        for detection in cls.detections:
            if detection.class_name == detections_type:
                count += 1
        return { 'result': count == expected_value }

    @classmethod
    def center_is_near_of(
            cls, detection : Detection, point : tuple[float, float], radius : float=0.05
        ) -> bool:
        distance = cls._get_distance_between_points(detection.middle_point, point)
        result = distance <= radius
        return {'result':result, 'distance':distance, 'center':detection.middle_point, 'point':point, 'radius':radius}

    @classmethod
    def horizontally_alling(cls, detections : list[Detection], tolerance = 0.05) -> bool:
        points = [detection.middle_point for detection in detections]
        average_y = sum([point[1] for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point[1] - average_y) > tolerance:
                result = False
        result = True
        return {'result':result, 'average point':average_y, 'points':points, 'tolerance':tolerance }

    @classmethod
    def vertically_alling(cls, detections : list[Detection], tolerance = 0.05) -> bool:
        points = [detection.middle_point for detection in detections]
        average_x = sum([point[0] for point in points]) / len(points)
        result = None
        for point in points:
            if abs(point[0] - average_x) > tolerance:
                result = False
        result = True
        return {'result':result, 'average point':average_x, 'points':points, 'tolerance':tolerance }

    @classmethod
    def inside(bigger : Detection, smaller : Detection):
        middle = smaller.middle_point
        ymin, xmin, ymax, xmax = bigger.bounding_box
        result = ymin <= middle[1] <= ymax and xmin <= middle[0] <= xmax
        return {'result':result, 'middle':middle, 'bounding_box':bigger.bounding_box}


    @classmethod
    def aspect_ratio(cls, detection : Detection, expected_ratio : float, tolerance : float = 0.1) -> bool:
        aspect_ratio = detection.width / detection.height
        result = abs(aspect_ratio - expected_ratio) <= tolerance
        return {'result':result, 'aspect_ratio':aspect_ratio, 'expected_ratio':expected_ratio, 'tolerance':tolerance}

    # Below methods cannot be used as checks

    @classmethod
    def _get_distance_between_points(
            cls,
            point1 : tuple[float, float], point2 : tuple[float, float]
        ) -> float:
        return sqrt(
            (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2
        )
    
    @classmethod
    def _sort_vertically(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point[1])

    @classmethod
    def _sort_horizontally(cls, detections : list[Detection]) -> list[Detection]:
        return sorted(detections, key=lambda detection: detection.middle_point[0])


# First stage
class CpfBlockChecker(Checker):
    EXPECTED_COUNT =   1
    EXPECTED_COLUMN_COUNT = 11
    EXPECTED_AVERAGE_MIDDLE_POINT = (0.34431372549019607843137254901961, 0.30139720558882235528942115768463)

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []
        
        cls.checks.append( {"cpf_block_count":cls.count(cls.EXPECTED_COUNT, 'cpf_block')} )
        cpf_block_detection = cls.detections[0]
        cls.checks.append( {"cpf_column_count":cls.count(cls.EXPECTED_COLUMN_COUNT, 'cpf_column')} )
        cls.checks.append( {"cpf_block_center_is_near_of":cls.center_is_near_of(cpf_block_detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT)} )
        # cls.checks.append( {"colums_horizontaly_aligned":cls.horizontally_alling('cpf_column')} )

        return cls.checks

class QuestionsBlockChecker(Checker):
    EXPECTED_QUESTIONS_BLOCK_COUNT = 6
    EXPECTED_AVERAGE_MEDDLE_POINTS = [
        (.6, .2), (.6, .4), (.6, .6), (.6, .8), ( .6, 1), (.6, 1.2)
    ] #TODO: get real values here
    UPPER_TREE_BLOCKS : list[Detection] = []
    LOWER_TREE_BLOCKS : list[Detection] = []

    @classmethod
    def perform_checks(cls):
        if len(cls.detections) == 0:
            return []

        cls._sort_top_left_to_bottom_right(cls.detections)

        cls.checks.append( {"question_block_count":cls.count(cls.EXPECTED_QUESTIONS_BLOCK_COUNT, 'questions_block')} )
        cls.checks.append( {"upper_tree_blocks_aling_horizontally":cls.horizontally_alling(cls.UPPER_TREE_BLOCKS, tolerance=0.01)} )
        cls.checks.append( {"lower_tree_blocks_aling_horizontally":cls.horizontally_alling(cls.LOWER_TREE_BLOCKS, tolerance=0.01)} )
        cls.checks.append( {"left_most_blocks_aling_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[0], cls.LOWER_TREE_BLOCKS[0]], tolerance=0.01)} )
        cls.checks.append( {"midle_blocks_aling_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[1], cls.LOWER_TREE_BLOCKS[1]], tolerance=0.01)} )
        cls.checks.append( {"right_most_blocks_align_vertically":cls.vertically_alling([cls.UPPER_TREE_BLOCKS[2], cls.LOWER_TREE_BLOCKS[2]], tolerance=0.01)} )

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
    pass

class QuestionLineChecker(Checker):
    EXPECTED_QUESTION_LINE_COUNT =          10
    EXPECTED_QUESTION_SELECTED_BALL_COUNT =  1
    pass

class QuestionNumberChecker(Checker):
    EXPECTED_QUESTION_NUMBER_COUNT =        10
    pass

class SelectedBallChecker(Checker):
    pass

class UnselectedBallChecker(Checker):
    pass