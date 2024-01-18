from __future__ import annotations

import json

from builder.dataclasses import Block, BuilderContext
from aux import log


#config vars
PROVA = 'PS'
CONTINUE_ON_FAIL = False


logger = log.get_new_logger('builder')

# init function
def load_builder():
    global _builder
    if PROVA == 'SIMUENEM':
        raise NotImplementedError('SIMUENEM is not implemented yet')
    elif PROVA == 'SIMUFSC':
        raise NotImplementedError('SIMUFSC is not implemented yet')
    elif PROVA == 'PS':
        import builder.ps_alunos_builder as _builder


# main function
def build(path, status='success') -> dict:

    logger.info(f'building report for {path.name}...')

    context = BuilderContext()

    with open(path) as f:
        data : dict = json.load(f)
    
    logger.info('getting cpf block...')
    for name in data:
        if 'cpf' in name.lower():
            cpf_nome = name
            cpf_detections = data.pop(cpf_nome)
            context.cpf_block = Block(name=cpf_nome, detections=cpf_detections)
            logger.info(f'cpf block found: {cpf_nome}')
            break
    else:
        logger.error(f'cpf block not found for {path.name}')
        if not CONTINUE_ON_FAIL:
            raise Exception(f'cpf block not found for {path.name}')
    
    logger.info('getting questions blocks...')
    for i, n in enumerate(data):
        logger.info(f'adding block to context: {n}')
        context.questions_block.append(Block(name=n, order=i, detections=data[n]))

    return _builder.build(context, status=status)

# tools class to make the report
class Builder():

    @classmethod
    def get_cpf(cls, cpf_block : Block) -> str:
        logger.debug(f'getting cpf: {cpf_block.name}')
        cpf = ''
        ball_columns = cls.get_ball_columns(0.02, cpf_block.detections)

        cont = 0
        while cont < 11:
            try:
                answer_index = cls.get_selected_ball_position('columns', 11, ball_columns[cont])
            except IndexError:
                break
            if answer_index is not None:
                cpf += str(answer_index)
            else:
                cpf += 'X'
            cont += 1
        if cont < 11:
            cpf += 'X' * (11 - cont)
        return cpf

    @classmethod
    def get_ball_lines(cls, distance_threshold, detections : list[dict]):
        return cls._get_balls('y', distance_threshold, detections)

    @classmethod
    def get_ball_columns(cls, distance_threshold, detections : list[dict]):
        return cls._get_balls('x', distance_threshold, detections)

    @classmethod
    def get_selected_ball_position(cls, type, num_elements, detections : list[dict]) -> list[dict]:
        logger.debug(f'getting selected ball position in {type}...')
        logger.debug(f'detections: {detections}')
        if len(detections) != num_elements:
            return None
        axis = 'y' if type == 'columns' else 'x'
        sorted_detections = cls._sort_axis(axis, detections)
        cont = 0
        while True:
            try:
                if sorted_detections[cont]['class_id'] == 'selected_ball':
                    break
            except IndexError:
                return None
            else:
                cont += 1
        return cont


    @classmethod
    def _get_balls(cls, axis, distance_threshold, detections : list[dict]) -> list[list[dict]]:
        sorted_detections = cls._sort_axis(axis, detections)
        index = 3 if axis == 'y' else 2
        ball_lines = []

        ball_line = [sorted_detections.pop(0)]
        while len(sorted_detections) > 0:
            if abs(
                sorted_detections[0]['bounding_box'][index] - ball_line[-1]['bounding_box'][index]
            ) > distance_threshold:
                ball_lines.append(ball_line)
                ball_line = [sorted_detections.pop(0)] 
            else:
                ball_line.append(sorted_detections.pop(0))
        ball_lines.append(ball_line)

        return ball_lines

    @classmethod
    def _sort_axis(cls, axis : str, data : list[dict]) -> list[dict]:
            if axis.lower() == 'y':
                return sorted(data, key=lambda d: d['bounding_box'][3])
            elif axis.lower() == 'x':
                return sorted(data, key=lambda d: d['bounding_box'][2])
        

    