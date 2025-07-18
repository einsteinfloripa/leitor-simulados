from __future__ import annotations

from abc import ABC, abstractmethod

from core.definitions.enums import TestType
from core.definitions.question import Question
from core.definitions.blocks import Block
from core.detection import Detection

from .tools import get_lines, get_columns, get_selected_balls_index


# TODO: It would be better if the full report was returned
class Builder(ABC):
    """
    Abstract base class for builders, defining the required methods 
    for processing CPF and question blocks.
    """

    ## Dispatcher Constructor ##
    @classmethod
    @abstractmethod
    def from_test_type(cls, test_type: TestType) -> Builder:
        """
        Returns the appropriate Builder subclass based on the test type.

        Parameters
        ----------
        test_type : TestType
            The test type used to determine the builder.

        Returns
        -------
        Builder
            The corresponding Builder subclass.

        Raises
        ------
        NotImplementedError
            If the test type is not supported.
        """
        if test_type in {TestType.PS_ALUNOS, TestType.SIMULINHO}:
            from core.builder.ps_alunos_builder import PSAlunosBuilder
            return PSAlunosBuilder
        elif test_type == TestType.SIMUFSC:
            from core.builder.simufsc_builder import SimufscBuilder
            return SimufscBuilder
        else:
            raise NotImplementedError(f"Test type {test_type} not implemented")

    ## Main Virtual Functions ##
    @classmethod
    @abstractmethod
    def resolve_cpf(cls, cpf_block: Block, *args, **kwargs) -> str:
        """
        Resolves the CPF from the given block.

        If no digit is detected, it must return 'X' in place of the missing digit.

        Parameters
        ----------
        cpf_block : Block
            The block containing CPF-related detections.

        Returns
        -------
        str
            The resolved CPF as a string of 11 characters.

        Raises
        ------
        NotImplementedError
            Must be implemented by subclasses.
        """
        pass

    @classmethod
    @abstractmethod
    def resolve_question_block(cls, questions_block: Block, *args, **kwargs) -> list[Question]:
        """
        Resolves the questions detected in the given block.

        Parameters
        ----------
        questions_block : Block
            The block containing detected questions.

        Returns
        -------
        list[Question]
            A list of detected questions.

        Raises
        ------
        NotImplementedError
            Must be implemented by subclasses.
        """
        pass

    ## Standard CPF Build Function ##
    @staticmethod
    def STANDARD_BUILD_CPF_FUNCTION(cpf_block: Block) -> str:
        """
        Standard method to resolve a CPF from a given block.

        It processes the CPF block by detecting selected/unselected balls,
        extracting the corresponding digits, and ensuring valid formatting.

        Parameters
        ----------
        cpf_block : Block
            The block containing CPF-related detections.

        Returns
        -------
        str
            The resolved CPF as an 11-character string.

        Raises
        ------
        ValueError
            If the provided block is not a CPF block.
        """
        if cpf_block.root_detection.class_type is not Detection.Type.CPF_BLOCK:
            raise ValueError("The provided block must be a CPF block.")

        # Get all number detections within the CPF block
        detections = cpf_block.container.get_by_type(
            [Detection.Type.SELECTED_BALL, Detection.Type.UNSELECTED_BALL],
            to_list=True
        )

        # Group detections into lines and columns
        lines = get_lines(detections, 0.05)
        columns = get_columns(detections, 0.02)

        # Ensure the CPF block contains the correct structure (10 lines, 11 columns)
        if len(lines) != 10 or len(columns) != 11:
            return "XXXXXXXXXXX"  # Invalid CPF

        # Get max Y-values of each line to determine digit placement
        max_values = [max(d.bounding_box[3] for d in line) for line in lines]

        # Construct CPF by detecting selected balls in each column
        cpf = ""
        for column in columns:
            selected_indices = get_selected_balls_index(column)

            # If there is more than one selected ball or none, mark as 'X'
            if len(selected_indices) != 1:
                cpf += "X"
                continue

            selected_ball = column[selected_indices[0]]

            # Determine the corresponding digit by comparing Y-values
            for i, val in enumerate(max_values):
                if selected_ball.bounding_box[3] <= val:
                    cpf += str(i)
                    break

        return cpf
