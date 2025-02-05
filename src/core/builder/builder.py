from __future__ import annotations

from abc import ABC, abstractmethod

from utils import log
from definitions.question import TestType
from definitions.test_defs import Question
from definitions.geometry import Axis
from core.builder.ps_alunos_builder import PSAlunosBuilder
from core.builder.simufsc_builder import SimufscBuilder
from core.builder.data_structs import Block
from core.detection import DetectionCoords, Detection

logger = log.get_new_logger('builder')

# tools class to make the report
class Builder(ABC):
    """
    The base class for the builders. It has the tool functions to build
    the CPF and the questions blocks reports.
    """

    ## Dispacher Constructor ##
    @classmethod
    def from_test_type(cls, test_type : TestType) -> Builder:
        if test_type == TestType.PS:
            return PSAlunosBuilder
        elif test_type == TestType.SIMUFSC:
            return SimufscBuilder
        else:
            raise NotImplementedError(f'Test type {test_type} not implemented')

    ## Main Virtual Functions ##
    @abstractmethod
    @classmethod
    def resolve_cpf(
            cls,
            cpf_block : Block,
            *args,
            **kwargs
        ) -> str:
        """
        This funciton must be implemented and must return the detected CPF value
        for the given cpf block.
        
        *if no digit was detected, it must return 'X' in the place of the digit.
        """
        pass

    @abstractmethod
    @classmethod
    def resolve_question_block(
            cls,
            questions_block : Block,
            *args,
            **kwargs
        ) -> list[Question]:
        """
        This function must be implemented and must return the detected questions
        in the given block.
        """
        pass   


    ## Standert Build function ##
    @classmethod
    def STANDART_BUILD_CPF_FUNCTION(
            cls,
            cpf_block : Block
        ):
        logger.debug(f'build_cpf : {cpf_block.root_detection.name}')
        max_values = cls._get_cpf_lines_max_y_value(cpf_block)
        if max_values is None:
            return "XXXXXXXXXXX"
        columns = cls._group_balls(Axis.HORIZONTAL, 0.02, cpf_block.detections)
        # Filter fake columns TODO: implement a better solution
        columns = [column for column in columns if len(column) > 2]
        if len(columns) != 11:
            return "XXXXXXXXXXX"
        cpf = ''

        for i, column in enumerate(columns):
            selected_ball = cls._have_unique_selected_ball(column)
            if selected_ball is None:
                cpf += 'X'
                continue

            for i, val in enumerate(max_values):
                if selected_ball['bounding_box'][3] <= val:
                    cpf += str(i)
                    break
        
        return cpf


    ## Tool functions ##
    @classmethod
    def _group_balls(cls,
            axis : Axis,
            distance_threshold : float,
            detections : list[DetectionCoords]
        ) -> list[list[DetectionCoords]]:
        # Sort the detections in the given axis
        sorted_detections = cls._sort_axis(axis, detections)
        # Select the index of the axis to be used
        index = 3 if axis == Axis.VERTICAL else 2
        # Group the detections
        groups = []
        group = [sorted_detections.pop(0)]
        while len(sorted_detections) > 0:
            last_inserted = group[-1]
            next_detection = sorted_detections[0]
            if next_detection.internal_bbox[index] - last_inserted.internal_bbox[index]\
                  > distance_threshold:
                groups.append(group)
                group = [sorted_detections.pop(0)] 
            else:
                group.append(sorted_detections.pop(0))
        groups.append(group)

        return groups

    @classmethod
    def _sort_axis(cls, axis : Axis, detections : list[DetectionCoords]) -> list[DetectionCoords]:
            if axis == Axis.VERTICAL:
                return sorted(detections, key=lambda d: d.internal_bbox.p_min.y)
            elif axis == Axis.HORIZONTAL:
                return sorted(detections, key=lambda d: d.internal_bbox.p_min.x)
    
    @classmethod
    def _get_selected_ball_position(
            cls,
            axis : Axis,
            expected_num_elements : int,
            detections : list[DetectionCoords]
        ) -> int:
        # Check if the number of detections is correct
        if len(detections) != len(expected_num_elements):
            return None
        # Sort the detections
        sorted_detections = cls._sort_axis(axis, detections)
        # Get the selected ball position
        try:
            cont = 0
            while True:
                if sorted_detections[cont]['class_id'] == 'selected_ball':
                    break
                cont += 1
            return cont
        except IndexError:
            return None
    
    @classmethod
    def _get_cpf_lines_max_y_value(
            cls,
            cpf_block : Block
        ) -> list[float]:
        """
        This function gets the maximum value of the y axis of each line of the CPF
        (i. e. the lowest detection of each number in the cpf block).
        """
        max = []
        lines : list[list[DetectionCoords]] =\
            cls._group_balls(Axis.VERTICAL, 0.05, cpf_block.detections)
        if len(lines) != 10:
            return None        
        for line in lines:
            max.append(line[-1].internal_bbox.p_max.y)
        return max

    @classmethod
    def _have_unique_selected_ball(
            cls,
            detections : list[DetectionCoords]
        ) -> DetectionCoords | None:
        cont = 0
        detection = None
        for d in detections:
            if d.class_type == Detection.Type.SELECTED_BALL:
                cont += 1
                detection = d
        if cont == 1:
            return detection
        return None
