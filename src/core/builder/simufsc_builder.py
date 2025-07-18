from __future__ import annotations

from copy import deepcopy

from core.definitions.geometry import Axis
from core.definitions.question import Question, NumericAnswer
from core.definitions.blocks import Block
from core.detection import Detection

from utils.log import LoggingSystem

from .base import Builder
from .tools import (
    sort_axis,
    get_selected_balls_index, 
    get_columns
)


class SimufscBuilder(Builder):
    """
    Builder class for processing PSAlunos question blocks.
    """

    _logger = LoggingSystem.get_new_logger("Core.SimufscBuilder")

    @classmethod
    def resolve_cpf(cls, block: Block) -> str:
        """
        Uses the standard build CPF function to resolve the CPF from the given block.
        """
        return cls.STANDARD_BUILD_CPF_FUNCTION(block)

    @classmethod
    def resolve_question_block(cls, block: Block) -> list[Question]:
        """
        Processes a question block and generates a list of Question objects representing
        each question's selected answer.

        This method extracts ball detections from the block container, groups them into lines,
        sorts the balls in each line, and determines the selected answer based on the index
        of the selected ball. It also handles cases where the line is incomplete or has multiple
        selected balls.

        Parameters
        ----------
        block : Block
            The block containing ball detections for a set of questions.

        Returns
        -------
        list[Question]
            A list of Question objects with question numbers, answers, and position points.
        """
        # Extract ball detections for both selected and unselected balls
        ball_detections = block.container.get_by_type(
            [
                Detection.Type.SELECTED_BALL,
                Detection.Type.UNSELECTED_BALL
            ],
            to_list=True
        )

        block_report: list[Question] = []

        # Group ball detections into lines (rows)
        ball_columns = get_columns(ball_detections, 0.05)

        # Get the point to draw the answer
        writing_anchor_point = deepcopy(
            block.root_detection.global_pixel_bounding_box.p_min
        )
        # add an offset on the y-axis to avoid overlapping with the block's root detection
        writing_anchor_point.y -= block.root_detection.pixel_height // 10

        # CASE 1: If wrong number of columns, we cannot process the block correctly
        # Add a guard to ensure we have enough columns
        if len(ball_columns) != 2:
            cls._logger.warning(
                f"Insufficient columns detected in block {block.order}. Expected at least 2, found {len(ball_columns)}."
            )
            block_report.append(
                    Question(
                        block.order, 
                        NumericAnswer.NULL(),  # Placeholder answer
                        writing_anchor_point  # Placeholder position
                    )
                )
            return block_report
        

        # CASE 2: Wrong number of balls in one of the columns
        elif len(ball_columns[0]) != 10 or len(ball_columns[1]) != 10:
            cls._logger.warning(
                f"Incorrect number of balls in columns for block {block.order}. "
                f"Expected 10, found {len(ball_columns[0])} in column 1 and {len(ball_columns[1])} in column 2."
            )
            block_report.append(
                Question(
                    block.order,  
                    NumericAnswer.NULL(),  # Placeholder answer
                    writing_anchor_point  # Placeholder position
                )
            )
            return block_report


        # Get the index of the selected balls in each column
        ball_columns[0] = sort_axis(ball_columns[0], Axis.VERTICAL)
        ball_columns[1] = sort_axis(ball_columns[1], Axis.VERTICAL)
        first_column_index = get_selected_balls_index(ball_columns[0])
        second_column_index = get_selected_balls_index(ball_columns[1])
        
        # CASE 3: Empty answer
        if not first_column_index or not second_column_index:
            cls._logger.warning(
                f"Empty answer detected in block {block.order}. "
                f"First column index: {first_column_index}, Second column index: {second_column_index}."
            )
            block_report.append(
                Question(
                    block.order,  
                    NumericAnswer.NOT_ANSWERD(),  # Placeholder answer
                    writing_anchor_point  # Placeholder position
                )
            )
            return block_report

        # CASE 4: Multiple answers selected
        if len(first_column_index) > 1 or len(second_column_index) > 1:
            cls._logger.warning(
                f"Multiple answers selected in block {block.order}. "
                f"First column index: {first_column_index}, Second column index: {second_column_index}."
            )
            block_report.append(
                Question(
                    block.order,  
                    NumericAnswer.NULL(),  # Placeholder answer
                    writing_anchor_point  # Placeholder position
                )
            )
            return block_report
        
        # CASE 5: Valid answer
        first_answer = first_column_index[0] 
        second_answer = second_column_index[0]
        cls._logger.debug(
            f"Block {block.order} has answers: First Column: {first_answer}, Second Column: {second_answer}."
        )
        answer = first_answer * 10 + second_answer
        block_report.append(
            Question(
                block.order,  
                NumericAnswer(answer),  # Valid answer
                writing_anchor_point  # Position to write the answer
            )
        )
        return block_report

