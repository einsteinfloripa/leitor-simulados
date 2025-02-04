
from builder.data_classes import BuilderContext, Block
from builder import Builder

from utils import log

logger = log.get_new_logger('ps_alunos_builder')


def build(context : BuilderContext, status, ec) -> None:
    logger.debug('building report...')    
    # Create a dictionary to store the report
    report = {}
    # Set the pipeline if the error correction was set
    # TODO: I think this can be change to a flag set
    if 'cpf' in ec: SimufscBuilder.set_cpf_func(SimufscBuilder.standart_build_cpf_ec)
    else: SimufscBuilder.set_cpf_func(SimufscBuilder.standart_build_cpf) 
    if 'questions' in ec: raise NotImplementedError('Error correction for questions block not implemented yet')
    else: SimufscBuilder.set_qb_func(SimufscBuilder.build_questions_block)
    # Build the cpf block if exists
    if context.cpf_block is not None and context.cpf_block.detections:
        logger.debug('building cpf from cpf_block...')
        report['cpf'] = SimufscBuilder.build_cpf(context.cpf_block)
    else:
        report['cpf'] = 'XXXXXXXXXXX'
    # Build the questions blocks
    logger.debug('building questions from questions_blocks...')
    for block in context.questions_block:
        block_number = block.name.split('.')[0][-2:]
        block_number = str(int(block_number) + 1)
        report.update(
            {
                block_number:SimufscBuilder.build_qb(block)
            })
    # Return the report
    return report


class SimufscBuilder(Builder):

    @classmethod
    def build_questions_block(cls, block : Block):
        if not block.detections:
            return 'NAO DETECTADO'
        logger.debug(f'building block: {block.name}')
        # Set variables
        block_number = block.order + 1 # Number of the Question Block
        block_report = 0               # Stores the answers of a single block
        # Get the lines of balls
        line_balls = cls.get_ball_lines(0.05, block.detections)
        # TODO: Soluçao fraca, se tiver tempo implementar uma melhor
        # remove a primeira linha no caso de uma letra ser confundida com um número
        if len( line_balls[0] ) < 2:
            line_balls.pop(0)
        # Now sort the balls per column
        lines = [l for line in line_balls for l in line]
        column_balls = cls.get_ball_columns(0.05, lines)
        # Iterate over the lines and get the selected ball
        # Calculate the answer with the balls position
        for i in range(2):
            # Get the index position of the selected ball
            selected_ball_index = cls._get_selected_ball_position('columns', 10, column_balls[i])
            # i = 0 -> mult = 10; i = 1 -> mult = 1
            multyplier = 10**((i+1)%2)
            # Calculate the answer
            if selected_ball_index is not None:
                block_report += selected_ball_index * multyplier # Left digit are decimals
            else:
                block_report = 'NAO DETECTADO'
                break
        # Return the block report
        return str(block_report)
