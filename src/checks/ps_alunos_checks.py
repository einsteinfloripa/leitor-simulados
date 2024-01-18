from __future__ import annotations

from aux.log import checks_logger as logger

from aux.object_detection import Detection
from aux.data_classes import FloatBoundingBox, FloatPoint
from checks import Checker, logger


def setup_detections(detections : list[Detection], filter_detections : bool, stage : int) -> None:
        if stage == 1:
            CHECKERS_MAP = {'cpf_block':CpfBlockChecker, 'questions_block':QuestionsBlockChecker}
        elif stage == 2:
            CHECKERS_MAP = {'cpf_column':CpfColumnChecker, 'question_line':QuestionLineChecker,
            'selected_ball':SelectedBallChecker, 'unselected_ball':UnselectedBallChecker,
            'question_number':QuestionNumberChecker
        }
        logger.debug(f'Setup for detections')
        # clear old detections and reset fail flag
        for check_class in CHECKERS_MAP.values():
            check_class.detections.clear()
            check_class.fail = False

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
                if hasattr(cls, 'clean_detections'):
                    cls.clean_detections()


def perform_checks(stage : int) -> None:
    if stage == 1:
        CpfBlockChecker.perform_checks()
        QuestionsBlockChecker.perform_checks()
    elif stage == 2:
        CpfColumnChecker.perform_checks()
        QuestionLineChecker.perform_checks()
        SelectedBallChecker.perform_checks()
        UnselectedBallChecker.perform_checks()
        QuestionNumberChecker.perform_checks()
        QuestionLineClusterChecker.perform_checks()



################# FIRST STAGE CHECKS #####################
class CpfBlockChecker(Checker):
    EXPECTED_COUNT =           1    
    EXPECTED_ASPECT_RATIO = 0.5847
    ASPECT_RATIO_TOLERANCE = 0.1

    EXPECTED_AVERAGE_MIDDLE_POINT : FloatPoint = FloatPoint(0.3443, 0.3013)
    MIDDLE_POINT_RADIUS_TOLERANCE = 0.05 # 5% of the image height

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.info(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.center_is_near_of(detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT, radius=cls.MIDDLE_POINT_RADIUS_TOLERANCE, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'cpf_block')
        for detection in cls.detections:
            cls.center_is_near_of(detection, cls.EXPECTED_AVERAGE_MIDDLE_POINT, radius=cls.MIDDLE_POINT_RADIUS_TOLERANCE)
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=0.1)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')


class QuestionsBlockChecker(Checker):
    #count
    EXPECTED_COUNT = 6
    #position
    EXPECTED_AVERAGE_MIDDLE_POINTS = [
        FloatPoint(0.2101, 0.5249), FloatPoint(0.5, 0.5249), FloatPoint(0.7713, 0.5249),
        FloatPoint(0.2101, 0.7245), FloatPoint(0.5, 0.7245), FloatPoint(0.7713, 0.7245)
    ]
    MIDDLE_POINTS_RADIUS = 0.05 # 5% of the image height
    #aspect ratio
    EXPECTED_ASPECT_RATIO =  1.1896
    ASPECT_RATIO_TOLERANCE = 0.15
    #aux
    UPPER_TREE_BLOCKS : list[Detection] = []
    LOWER_TREE_BLOCKS : list[Detection] = []

    
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
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for i, detection in enumerate(cls.detections):
            # Position
            cls.center_is_near_of(cls.sorted_detections[i], cls.EXPECTED_AVERAGE_MIDDLE_POINTS[i], radius=cls.MIDDLE_POINTS_RADIUS, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'questions_block'),
        cls.horizontally_alling(cls.UPPER_TREE_BLOCKS, tolerance=0.01),
        cls.horizontally_alling(cls.LOWER_TREE_BLOCKS, tolerance=0.01),
        try:
            cls.vertically_alling([cls.UPPER_TREE_BLOCKS[0], cls.LOWER_TREE_BLOCKS[0]], tolerance=0.01),
            cls.vertically_alling([cls.UPPER_TREE_BLOCKS[1], cls.LOWER_TREE_BLOCKS[1]], tolerance=0.01),
            cls.vertically_alling([cls.UPPER_TREE_BLOCKS[2], cls.LOWER_TREE_BLOCKS[2]], tolerance=0.01),
        except IndexError:
            pass
        for point, detection in zip(cls.EXPECTED_AVERAGE_MIDDLE_POINTS, cls.sorted_detections):
            cls.center_is_near_of(detection, point, radius=cls.MIDDLE_POINTS_RADIUS)
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')

################# SECOND STAGE CHECKS #####################
class CpfColumnChecker(Checker):
    #count
    EXPECTED_COUNT = 11
    #position
    EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
        x_min=0.1167, y_min=0.4259, x_max=0.9867, y_max=0.5555
    )
    #allignment
    ALLIGNMENT_TOLERANCE = 0.15 # 15% of the image height 
    #aspect ratio
    EXPECTED_ASPECT_RATIO =  9.5
    ASPECT_RATIO_TOLERANCE = 0.2

    
    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.inside_box(detection, cls.EXPECTED_BOUNDRIES, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'cpf_column'),
        cls.horizontally_alling(cls.detections, tolerance=cls.ALLIGNMENT_TOLERANCE),
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        cls.logger.info(f'[ PASSED ]')


class QuestionLineChecker(Checker):
    #count
    EXPECTED_COUNT = 10
    #position
    EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
        x_min=0.4, y_min=0.17, x_max=0.6, y_max=0.96
    )
    #allignment
    ALLIGNMENT_TOLERANCE = 0.10 # 10% of the image height
    #aspect ratio
    EXPECTED_ASPECT_RATIO =  0.09
    ASPECT_RATIO_TOLERANCE = 0.8 

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.inside_box(detection, cls.EXPECTED_BOUNDRIES, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'question_line'),
        cls.vertically_alling(cls.detections, tolerance=cls.ALLIGNMENT_TOLERANCE)
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')


class QuestionNumberChecker(Checker):
    #count
    EXPECTED_COUNT = 10
    #position
    EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
        x_min=0.09, y_min=0.17, x_max=0.15, y_max=0.96
    )
    #allignment
    ALLIGNMENT_TOLERANCE = 0.10 # 10% of the image height
    #aspect ratio
    EXPECTED_ASPECT_RATIO =  0.574
    ASPECT_RATIO_TOLERANCE = 0.8

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.inside_box(detection, cls.EXPECTED_BOUNDRIES, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):
        
        cls.count(cls.EXPECTED_COUNT, 'question_number'),
        cls.vertically_alling(cls.detections, tolerance=cls.ALLIGNMENT_TOLERANCE)
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')


class SelectedBallChecker(Checker):
    #aspect ratio
    EXPECTED_ASPECT_RATIO =  1
    ASPECT_RATIO_TOLERANCE = 0.3

    @classmethod
    def _precheck_setup(cls):
        if cls.IMG_INSTANCE.cropped_by == 'cpf_block':
            #count
            cls.EXPECTED_COUNT = 11
            #position
            cls.EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
                x_min=0.135, y_min=0.08, x_max=0.96, y_max=0.96
            )
        elif cls.IMG_INSTANCE.cropped_by == 'questions_block':
            #count
            cls.EXPECTED_COUNT = 10
            #position
            cls.EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
                    x_min=0.138, y_min=0.17, x_max=0.96, y_max=0.96
            )


    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.inside_box(detection, cls.EXPECTED_BOUNDRIES, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'selected_ball'),
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')


class UnselectedBallChecker(Checker):

    #aspect ratio
    EXPECTED_ASPECT_RATIO =  1
    ASPECT_RATIO_TOLERANCE = 0.3

    @classmethod
    def _precheck_setup(cls):
        if cls.IMG_INSTANCE.cropped_by == 'cpf_block':
            #count
            cls.EXPECTED_COUNT = 100
            #position
            cls.EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
                x_min=0.135, y_min=0.08, x_max=0.96, y_max=0.96
            )
        elif cls.IMG_INSTANCE.cropped_by == 'questions_block':
            #count
            cls.EXPECTED_COUNT = 40
            #position
            cls.EXPECTED_BOUNDRIES = FloatBoundingBox.from_floats(
                    x_min=0.138, y_min=0.17, x_max=0.96, y_max=0.96
            )

    @classmethod
    @Checker.has_detections
    def clean_detections(cls):
        cls.logger.debug(f'Cleaning detections...')
        cls.to_remove = []
        for detection in cls.detections:
            # Position
            cls.inside_box(detection, cls.EXPECTED_BOUNDRIES, filter=True)
            # Aspect Ratio
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE, filter=True)

        for detection in cls.to_remove:
            try:
                cls.IMG_INSTANCE.detections.remove(detection)
                cls.detections.remove(detection)
            except ValueError:
                continue

    @classmethod
    @Checker.has_detections
    def perform_checks(cls):

        cls.count(cls.EXPECTED_COUNT, 'unselected_ball'),
        for detection in cls.detections:
            cls.aspect_ratio(detection, cls.EXPECTED_ASPECT_RATIO, tolerance=cls.ASPECT_RATIO_TOLERANCE)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')


class QuestionLineClusterChecker(Checker):
    EXPECTED_SELECTED_BALL_COUNT =  1
    EXPECTED_UNSELECTED_BALL_COUNT =  4
    EXPECTED_QUESTION_NUMBER_COUNT = 1
    
    @classmethod
    def perform_checks(cls):
        cls._build_clusters()
        for cluster in cls.clusters:
            question_line = cluster['parent']
            for detection in cluster['children']:
                cls.contains(question_line, detection)

        if not cls.fail: cls.logger.warning(f'[ PASSED ]')

    @classmethod
    def _build_clusters(cls):
        selected_ball = cls._group_by_axis(SelectedBallChecker.get_detections(), axis='y', size=1)
        unselected_ball = cls._group_by_axis(UnselectedBallChecker.get_detections(), axis='y', size=4)
        question_number = cls._group_by_axis(QuestionNumberChecker.get_detections(), axis='y', size=1)
        question_line = QuestionLineChecker.get_detections()

        if not len(selected_ball) == len(unselected_ball) == len(question_number) == len(question_line):
            cls.logger.warning(f'[ FALIED ] _build_clusters : wrong number of detections')
            raise AssertionError(f'wrong number of detections')

        cls.clusters = []
        for i in range(len(selected_ball)):
            cluster = {'parent':None, 'children':[]}
            cluster['parent'] = question_line[i]
            cluster['childrem'] = selected_ball[i] + unselected_ball[i] + question_number[i]


