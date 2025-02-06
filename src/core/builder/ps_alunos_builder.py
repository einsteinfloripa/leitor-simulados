from.base import Builder
from builder.data_structs import Block

from definitions.question import Question, AlphaAnswer, NumericAnswer

from .tools import get_lines, get_selected_balls_index


class PSAlunosBuilder(Builder):
    # Map to convert the index of the selected ball to a letter

    @classmethod
    def resolve_cpf(cls, block : Block) -> str:
        return cls.STANDART_BUILD_CPF_FUNCTION(block)

    @classmethod
    def resolve_question_block(cls, block : Block) -> list[Question]:        
        # Set variables
        detections = block.container.get_detections()
        block_number = (block.order * 10) + 1 # Number of the Question Block
        block_report : list[Question] = []    # Stores the answers of a single block
        # Get the lines of balls
        line_balls = get_lines(detections, 0.05)
        # TODO:Soluçao fraca, se tiver tempo implementar uma melhor
        # Remove a primeira linha no caso de uma letra ser confundida com um número
        if len( line_balls[0] ) < 3:
            line_balls.pop(0)
        # Iterate over the lines and get the selected ball
        cont = 0
        while cont < 10:
            question_number = block_number + cont
            line = line_balls[cont]
            answer_index = get_selected_balls_index(line_balls[cont])
            # If the line has not 5 balls, or there are more the one selected ball
            if len(line) != 5 or len(answer_index) > 1:
                block_report.append(
                    Question(
                        question_number,
                        AlphaAnswer.NULL
                        )
                    )
                cont += 1
                continue
            # Check if there is not selected ball but the line has 5 balls
            if not answer_index and len(line) == 5:
                block_report.append(
                    Question(
                        question_number,
                        AlphaAnswer.NOT_ANSWERED
                        )
                    )
                cont += 1
                continue

            # Calculate the answer with the balls position
            block_report.append(
                Question(
                    question_number,
                    AlphaAnswer(answer_index[0] + 1)
                    )
                )
            cont += 1
        # Return the block report
        return block_report

