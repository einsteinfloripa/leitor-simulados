from __future__ import annotations

from abc import ABC, abstractmethod

from definitions.question import TestType
from definitions.test_defs import Question
from core.builder.ps_alunos_builder import PSAlunosBuilder
from core.builder.simufsc_builder import SimufscBuilder
from core.builder.data_structs import Block


class Builder(ABC):
    """
    The base class for the builders. It has the tool functions to build
    the CPF and the questions blocks reports.
    """

    ## Dispacher Constructor ##
    @classmethod
    @abstractmethod
    def from_test_type(cls, test_type : TestType) -> Builder:
        if test_type == TestType.PS:
            return PSAlunosBuilder
        elif test_type == TestType.SIMUFSC:
            return SimufscBuilder
        else:
            raise NotImplementedError(f'Test type {test_type} not implemented')

    ## Main Virtual Functions ##
    @classmethod
    @abstractmethod
    def resolve_cpf(
            cls,
            cpf_block : Block,
            *args,
            **kwargs
        ) -> str:
        """
        This funciton must be implemented and must return the detected CPF value
        for the given cpf block.
        
        *if no digit was detected, it must return 'X' in the place of the digit.
        """
        pass

    @classmethod
    @abstractmethod
    def resolve_question_block(
            cls,
            questions_block : Block,
            *args,
            **kwargs
        ) -> list[Question]:
        """
        This function must be implemented and must return the detected questions
        in the given block.
        """
        pass   