
from builder.dataclasses import BuilderContext, Block
from builder import Builder

from aux import log

logger = log.get_new_logger('ps_alunos_builder')


def build(context : BuilderContext, status, ec) -> None:

    logger.debug('building report...')    

    report = {}


    if 'cpf' in ec: PSAlunosBuilder.set_cpf_ec_pipeline(context)

    if context.cpf_block is not None:
        logger.debug('building cpf from cpf_block...')
        report['cpf'] = PSAlunosBuilder.build_cpf(context.cpf_block)

    logger.debug('building questions from questions_blocks...')
    for block in context.questions_block:
        report.update(PSAlunosBuilder.build_questions_block(block))

    return report


class PSAlunosBuilder(Builder):

    LETTER_MAP = ['A', 'B', 'C', 'D', 'E']

    @classmethod
    def build_questions_block(cls, block : Block):
        logger.debug(f'building block: {block.name}')
        block_number = (block.order * 10) + 1

        block_report = {}

        line_balls = cls.get_ball_lines(0.05, block.detections)
        cont = 0
        while cont < 10:
            try:
                answer_index = cls._get_selected_ball_position('x', 5, line_balls[cont])
            except IndexError:
                for i in range(cont, 10):
                    block_report[block_number + i] = 'NAO DETECTADO'
                break

            if answer_index is not None:
                answer = cls.LETTER_MAP[answer_index]
            else:
                answer = 'NAO DETECTADO'

            block_report[block_number + cont] = answer
            cont += 1



        return block_report
