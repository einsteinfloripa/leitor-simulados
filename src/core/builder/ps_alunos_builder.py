from __future__ import annotations

from core.definitions.geometry import Axis, IntPoint, IntBoundingBox
from core.definitions.question import Question, AlphaAnswer
from core.definitions.blocks import Block
from core.detection import Detection

from utils.log import LoggingSystem

from .base import Builder
from .tools import get_lines, get_selected_balls_index, sort_axis


class PSAlunosBuilder(Builder):
    """
    Builder class for processing PSAlunos question blocks.
    """

    _logger = LoggingSystem.get_new_logger("Core.PSAlunosBuilder")

    @classmethod
    def resolve_cpf(cls, block: Block) -> str:
        """
        Resolves the CPF from the given block using a standard build CPF function.

        Parameters
        ----------
        block : Block
            The block from which to extract the CPF.

        Returns
        -------
        str
            The resolved CPF string.
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

        order_multiplier = block.order - 1
        block_number = (order_multiplier * 10) + 1  # First question number in this block
        block_report: list[Question] = []  # List to store processed questions

        # Group ball detections into lines (rows)
        line_balls = get_lines(ball_detections, 0.05)

        # Remove the first line if it is likely to be a letter mistaken for a number
        if line_balls and len(line_balls[0]) < 3:
            line_balls.pop(0)

        # Process each question line (expected 10 questions per block)
        for i in range(10):
            question_number = block_number + i
            line = sort_axis(line_balls[i], Axis.HORIZONTAL)

            # Initialize the location of the last ball's northeast point
            last_ball_ne_point = None
            if len(line) == 5:
                last_ball: Detection = line[-1]
                global_pixels: IntBoundingBox = last_ball.to_global_pixels()
                offset_x = last_ball.pixel_width
                offset_y = last_ball.pixel_height // 2
                last_ball_ne_point = IntPoint(
                    global_pixels.p_max.x + offset_x,
                    global_pixels.p_min.y + offset_y
                )
            elif len(line) > 0:
                last_ball: Detection = line[-1]
                global_pixels: IntBoundingBox = last_ball.to_global_pixels()
                offset_x = last_ball.pixel_width // 2
                offset_y = last_ball.pixel_height // 2
                last_ball_ne_point = IntPoint(
                    global_pixels.p_max.x + offset_x,
                    global_pixels.p_min.y + offset_y
                )

            # Get indexes of selected balls in the current line
            answer_index = get_selected_balls_index(line)

            # Check for invalid cases: incomplete line or multiple selections
            if len(line) != 5 or len(answer_index) > 1:
                cls._logger.warning(
                    f"Invalid line detected in block {block.order} at question {question_number} \
| image position: {last_ball_ne_point}."
                )
                block_report.append(
                    Question(
                        question_number,
                        AlphaAnswer.NULL,
                        last_ball_ne_point
                    )
                )
                continue

            # Check for the case when no ball is selected
            if not answer_index and len(line) == 5:
                cls._logger.info(
                    f"Black answer detected in block {block.order} at question {question_number} \
| image position: {last_ball_ne_point}."
                )
                block_report.append(
                    Question(
                        question_number,
                        AlphaAnswer.NOT_ANSWERED,
                        last_ball_ne_point
                    )
                )
                continue

            # Otherwise, calculate the answer based on the selected ball index
            answer = AlphaAnswer(answer_index[0] + 1)
            cls._logger.debug(
                f"Question {question_number} in block {block.order} has answer {answer}. \
| image position: {last_ball_ne_point}."
            )
            block_report.append(
                Question(
                    question_number,
                    answer,
                    last_ball_ne_point
                )
            )

        return block_report
