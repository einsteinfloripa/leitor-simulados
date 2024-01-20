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
def build(path, status, ec) -> dict:

    context = BuilderContext()
    #loading file
    try:
        with open(path) as f:
            data : dict = json.load(f)
    except FileNotFoundError as e:
        logger.error(f'File not found! : {path.resolve()}')
        if not CONTINUE_ON_FAIL:
            raise e
        return 'FILE NOT FOUND'
    #getting cpf block in the context
    logger.info('getting cpf block...')
    for name in data:
        if 'cpf' in name.lower():
            cpf_nome = name
            cpf_detections = data.pop(cpf_nome)
            context.cpf_block = Block(name=cpf_nome, detections=cpf_detections)
            logger.debug(f'cpf block found: {cpf_nome}')
            break
    else:
        logger.error(f'cpf block not found for {path.name}')
        if not CONTINUE_ON_FAIL:
            raise Exception(f'cpf block not found for {path.name}')
    #getting questions blocks in the context
    logger.info('getting questions blocks...')
    for i, block in enumerate(data):
        logger.debug(f'adding block to context: {block}')
        context.questions_block.append(Block(name=block, order=i, detections=data[block]))

    return _builder.build(context, status=status, ec=ec)

# tools class to make the report
class Builder():

    @classmethod
    def set_cpf_ec_pipeline(cls, context):
        cls.build_cpf = cls.build_cpf_ec


    @classmethod
    def build_cpf(cls, cpf_block : Block) -> str:
        logger.debug(f'build_cpf : {cpf_block.name}')
        cpf = ''
        ball_columns = cls.get_ball_columns(0.02, cpf_block.detections)

        cont = 0
        while cont < 11:
            try:
                answer_index = cls._get_selected_ball_position('columns', 10, ball_columns[cont])
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
    def build_cpf_ec(cls, cpf_block : Block):
        logger.debug(f'build_cpf_ec : {cpf_block.name}')
        max_values = cls._get_cpf_lines_max_y_value(cpf_block)
        if max_values is None:
            return "XXXXXXXXXXX"
        columns = cls.get_ball_columns(0.02, cpf_block.detections)
        if len(columns) != 11:
            return "XXXXXXXXXXX"
        cpf = ''

        for i, column in enumerate(columns):
            selected_ball = cls._have_unique_selected_ball(column)
            if selected_ball is None:
                cpf += 'X'
                continue

            for i, val in enumerate(max_values):
                if selected_ball['bounding_box'][3] <= val:
                    cpf += str(i)
                    break
        
        return cpf
        

    # aux functions
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
    
    @classmethod
    def _get_selected_ball_position(cls, type, num_elements, detections : list[dict]) -> list[dict]:
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
    def _get_cpf_lines_max_y_value(cls, cpf_block : Block) -> list[tuple[float, float]]:
        max = []
        lines = cls.get_ball_lines(0.05, cpf_block.detections)
        if len(lines) != 10:
            return None        
        for line in lines:
            max.append(line[-1]['bounding_box'][3])
        return max

    @classmethod
    def _have_unique_selected_ball(cls, detections : list[dict]) -> dict:
        cont = 0
        detection = None
        for d in detections:
            if d['class_id'] == 'selected_ball':
                cont += 1
                detection = d
        if cont == 1:
            return detection
        return None
