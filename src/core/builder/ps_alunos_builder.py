
from builder import Builder
from builder.data_structs import Block

from definitions.test_defs import Question
from definitions.geometry import Axis
from utils import log



class PSAlunosBuilder(Builder):
    # Map to convert the index of the selected ball to a letter

    @classmethod
    def resolve_cpf(cls, block : Block) -> str:
        return cls.STANDART_BUILD_CPF_FUNCTION(block)

    @classmethod
    def get_question_block_values(cls, block : Block) -> list[Question]:        
        # Set variables
        block_number = (block.order * 10) + 1 # Number of the Question Block
        block_report = {}                     # Stores the answers of a single block
        # Get the lines of balls
        line_balls = cls._get_balls(Axis.HORIZONTAL, 0.05, block.detections)
        # TODO:Soluçao fraca, se tiver tempo implementar uma melhor
        # remove a primeira linha no caso de uma letra ser confundida com um número
        if len( line_balls[0] ) < 3:
            line_balls.pop(0)
        # Iterate over the lines and get the selected ball
        cont = 0
        while cont < 10:
            # Get the index position of the selected ball
            try:
                answer_index = cls._get_selected_ball_position('x', 5, line_balls[cont])
            except IndexError:
                for i in range(cont, 10):
                    block_report[block_number + i] = 'NAO DETECTADO'
                break
            # Calculate the answer with the balls position
            if answer_index is not None:
                answer = cls.LETTER_MAP[answer_index]
            else:
                answer = 'NAO DETECTADO'
            # Store the answer and move to the next block
            block_report[block_number + cont] = answer
            cont += 1
        # Return the block report
        return block_report
