from __future__ import annotations
from abc import ABC, abstractmethod
import json

from builder.data_classes import Block, BuilderContext
from utils import log
from core.defs import TestType

logger = log.get_new_logger('builder')

# init function
def load_builder(test_type : TestType):
    global _builder
    if test_type == TestType.SIMUENEM:
        raise NotImplementedError('SIMUENEM is not implemented yet')
    elif test_type == TestType.SIMUFSC:
        import builder.simufsc_builder as _builder
    elif test_type == TestType.PS:
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
class Builder(ABC):
    """
    The base class for the builders. It has the tool functions to build
    the CPF and the questions blocks reports.
    """

    ## Virtual Functions ##
    @abstractmethod
    @classmethod
    def get_cpf_block_value(cls, cpf_block : Block, *args, **kwargs) -> str:
        """
        This funciton must be implemented and must return the detected CPF value
        
        *if no digit was detected, it must return 'X' in the place of the digit.
        """
        pass

    @abstractmethod
    @classmethod
    def get_qustion_block_values(cls, questions_block : list[Block], *args, **kwargs) -> list:
        pass   

    ## Build function ##

    @classmethod
    def STANDART_BUILD_CPF_FUNCTION(cls, cpf_block : Block):
        logger.debug(f'build_cpf_ec : {cpf_block.root_detection.name}')
        max_values = cls._get_cpf_lines_max_y_value(cpf_block)
        if max_values is None:
            return "XXXXXXXXXXX"
        columns = cls.get_ball_columns(0.02, cpf_block.detections)
        # Filter fake columns TODO: implement a better solution
        columns = [column for column in columns if len(column) > 2]
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


    ## Tool functions ##
    @classmethod
    def get_balls(cls,
            axis,
            distance_threshold,
            detections : list[dict]
        ) -> list[list[dict]]:
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
    def sort_axis(cls, axis : str, data : list[dict]) -> list[dict]:
            if axis.lower() == 'y':
                return sorted(data, key=lambda d: d['bounding_box'][3])
            elif axis.lower() == 'x':
                return sorted(data, key=lambda d: d['bounding_box'][2])
    
    @classmethod
    def get_selected_ball_position(cls, type, num_elements, detections : list[dict]) -> list[dict]:
        try:
            logger.debug(f'getting selected ball position in {type}...')
            logger.debug(f'detections: {detections}')
            if len(detections) != num_elements:
                return None
            axis = 'y' if type == 'columns' else 'x'
            sorted_detections = cls._sort_axis(axis, detections)
            cont = 0
            while True:
                if sorted_detections[cont]['class_id'] == 'selected_ball':
                    break
                cont += 1
            return cont
        except IndexError:
            return None
    
    @classmethod
    def get_cpf_lines_max_y_value(cls, cpf_block : Block) -> list[tuple[float, float]]:
        max = []
        lines = cls.get_ball_lines(0.05, cpf_block.detections)
        if len(lines) != 10:
            return None        
        for line in lines:
            max.append(line[-1]['bounding_box'][3])
        return max

    @classmethod
    def have_unique_selected_ball(cls, detections : list[dict]) -> dict:
        cont = 0
        detection = None
        for d in detections:
            if d['class_id'] == 'selected_ball':
                cont += 1
                detection = d
        if cont == 1:
            return detection
        return None
