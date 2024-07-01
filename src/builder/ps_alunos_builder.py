
from builder.dataclasses import BuilderContext, Block
from builder import Builder

from utils import log

logger = log.get_new_logger('ps_alunos_builder')


def build(context : BuilderContext, status, ec) -> None:
    logger.debug('building report...')    
    # Create a dictionary to store the report
    report = {}
    # Set the pipeline if the error correction was set
    if 'cpf' in ec: PSAlunosBuilder.set_cpf_func(PSAlunosBuilder.standart_build_cpf_ec)
    else : PSAlunosBuilder.set_cpf_func(PSAlunosBuilder.standart_build_cpf)
    if 'qb' in ec: raise NotImplementedError('Error correction for questions block not implemented yet')
    else : PSAlunosBuilder.set_qb_func(PSAlunosBuilder.build_questions_block)
    # Build the cpf block if exists
    if context.cpf_block is not None:
        logger.debug('building cpf from cpf_block...')
        report['cpf'] = PSAlunosBuilder.build_cpf(context.cpf_block)
    else:
        report['cpf'] = 'XXXXXXXXXXX'
    # Build the questions blocks
    logger.debug('building questions from questions_blocks...')
    for block in context.questions_block:
        report.update(PSAlunosBuilder.build_qb(block))
    # Return the report
    return report


class PSAlunosBuilder(Builder):
    # Map to convert the index of the selected ball to a letter
    LETTER_MAP = ['A', 'B', 'C', 'D', 'E']

    @classmethod
    def build_questions_block(cls, block : Block):
        logger.debug(f'building block: {block.name}')
        # Set variables
        block_number = (block.order * 10) + 1 # Number of the Question Block
        block_report = {}                     # Stores the answers of a single block
        # Get the lines of balls
        line_balls = cls.get_ball_lines(0.05, block.detections)
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
