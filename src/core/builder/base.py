from __future__ import annotations

from abc import ABC, abstractmethod

from definitions.test_defs import TestType
from definitions.question import Question

from core.builder.data_structs import Block

from definitions.geometry import Axis
from core.detection import Detection

from .tools import get_lines, get_columns, get_selected_balls_index

class Builder(ABC):
    """
    The base class for the builders. It shows what methods must be implemented.
    """

    ## Dispacher Constructor ##
    # Imports lazily to avoid circular imports
    @classmethod
    @abstractmethod
    def from_test_type(cls, test_type : TestType) -> Builder:
        if test_type == TestType.PS_ALUNOS or test_type == TestType.SIMULINHO:
            from core.builder.ps_alunos_builder import PSAlunosBuilder
            return PSAlunosBuilder
        else:
            raise NotImplementedError(f'Test type {test_type} not implemented')

    ## Main Virtual Functions ##
    @classmethod
    @abstractmethod
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

    @classmethod
    @abstractmethod
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
    @staticmethod
    def STANDART_BUILD_CPF_FUNCTION(
            cpf_block : Block
        ):
        # Check if the block is a cpf block
        if cpf_block.root_detection.class_type is not Detection.Type.CPF_BLOCK:
            raise ValueError('Must be a cpf block')
        # Get the max values of each number detection on the cpf block
        detections = cpf_block.container.get_by_type(
            [
                Detection.Type.SELECTED_BALL,
                Detection.Type.UNSELECTED_BALL
            ],
            to_list = True
        )
        lines = get_lines(detections, 0.05)
        # If the cpf block has not 10 lines, return a invalid cpf
        if len(lines) != 10:
            return "XXXXXXXXXXX"
        # Get the max values of each line (i.e. the max y value of each detection in the line)
        max_values = [
            max(
                [detection.bounding_box[3] for detection in line]
            ) for line in lines
        ]

        columns = get_columns(detections, 0.02)
        # Filter fake columns TODO: implement a better solution
        columns = [column for column in columns if len(column) > 1]
        # If the cpf block has not 11 columns, return a invalid cpf
        if len(columns) != 11:
            return "XXXXXXXXXXX"
        # Build the cpf
        cpf = ''
        for i, column in enumerate(columns):
            selected_balls_indeces = get_selected_balls_index(column)
            # More than one selected ball or no selected ball
            if len(selected_balls_indeces) != 1 or not selected_balls_indeces:
                cpf += 'X'
                continue
            # Get the selected ball based on y value
            for i, val in enumerate(max_values):
                selected_ball : Detection = column[selected_balls_indeces[0]]
                if selected_ball.bounding_box[3] <= val:
                    cpf += str(i)
                    break
        
        return cpf
   