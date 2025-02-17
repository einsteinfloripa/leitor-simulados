from core.definitions.geometry import Axis, IntPoint, IntBoundingBox
from core.definitions.question import Question, AlphaAnswer
from core.definitions.blocks import Block
from core.detection import Detection

from .base import Builder
from .tools import get_lines, get_selected_balls_index, sort_axis


class PSAlunosBuilder(Builder):
    # Map to convert the index of the selected ball to a letter

    @classmethod
    def resolve_cpf(cls, block : Block) -> str:
        return cls.STANDART_BUILD_CPF_FUNCTION(block)

    @classmethod
    def resolve_question_block(cls, block : Block) -> list[Question]:        
        # Set variables
        ball_detections = block.container.get_by_type(
            [
                Detection.Type.SELECTED_BALL,
                Detection.Type.UNSELECTED_BALL
            ],
            to_list = True
        )
        block_number = (block.order * 10) + 1 # Number of the Question Block
        block_report : list[Question] = []    # Stores the answers of a single block
        # Get the lines of balls
        line_balls = get_lines(ball_detections, 0.05)
        # TODO:Soluçao fraca, se tiver tempo implementar uma melhor
        # Remove a primeira linha no caso de uma letra ser confundida com um número
        if len( line_balls[0] ) < 3:
            line_balls.pop(0)
        # Iterate over the lines and get the selected ball
        cont = 0
        while cont < 10:
            # Get the number of the question to be analized
            question_number = block_number + cont
            # Sort the balls in the line by the x axis
            line = sort_axis(line_balls[cont], Axis.HORIZONTAL)
            # Stores the position of the last ball
            last_ball_ne_point = None
            if len(line) == 5:
                last_ball : Detection = line[-1]
                global_pixels : IntBoundingBox = last_ball.to_global_pixels()
                # Add offset so is not on top of the ball detections
                offset_x = last_ball.pixel_width
                offset_y = last_ball.pixel_height // 2
                last_ball_ne_point = IntPoint(
                    global_pixels.p_max.x + offset_x,
                    global_pixels.p_min.y + offset_y
                )
            # Get the index of the selected ball
            answer_index = get_selected_balls_index(line)
            # If the line has not 5 balls, or there are more the one selected ball
            if len(line) != 5 or len(answer_index) > 1:
                block_report.append(
                    Question(
                        question_number,
                        AlphaAnswer.NULL,
                        last_ball_ne_point
                        )
                    )
                cont += 1
                continue
            # Check if there is not selected ball but the line has 5 balls
            if not answer_index and len(line) == 5:
                block_report.append(
                    Question(
                            question_number,
                            AlphaAnswer.NOT_ANSWERED,
                            last_ball_ne_point
                        )
                    )
                cont += 1
                continue

            # Calculate the answer with the balls position
            block_report.append(
                Question(
                        question_number,
                        AlphaAnswer(answer_index[0] + 1),
                        last_ball_ne_point
                    )
                )
            cont += 1
        # Return the block report
        return block_report

