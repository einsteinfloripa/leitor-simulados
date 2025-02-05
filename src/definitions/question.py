from __future__ import annotations
from enum import Enum
from typing import Type

from dataclasses import dataclass
from definitions.test_defs import TestType

class AlphaAnswer(Enum):
    NULL = 0
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5

class BinaryAnswer(Enum):
    NULL = 0
    TRUE = 1
    FALSE = 2

class NumericAnswer:
    def __init__(self):
        self.value = -1
    
    def set(self, value : int):
        if value < 0:
            raise ValueError("Numeric answer must be non-negative.")
        if value > 99:
            raise ValueError("Numeric answer must be less than 100.")
        if not isinstance(value, int):
            raise ValueError("Numeric answer must be an integer.")
        self.value = value

@dataclass
class Question:
    """
    Base question class, used to store the number and answer of a question.
    """
    number : int
    answer : AlphaAnswer | NumericAnswer | BinaryAnswer | None = None




class TestQuestions:
    """
    This class is responsable for storing the answers of a test.
    """

    @classmethod
    def from_test_type(
            cls,
            test_type : TestType,
            owner_cpf : str = "XXXXXXXXXXX"
        ) -> Type[TestQuestions]:
        if test_type == TestType.PS:
            return PsQuestions(owner_cpf=owner_cpf)
        elif test_type == TestType.SIMULINHO:
            return SimulinhoQuestions(owner_cpf=owner_cpf)
        elif test_type == TestType.SIMUFSC:
            return SimufscQuestions(owner_cpf=owner_cpf)
        elif test_type == TestType.SIMUENEM:
            return SimuenemQuestions(owner_cpf=owner_cpf)
        else:
            raise NotImplementedError(f'Test type {test_type} not implemented')

    def __init__(self, test_type : TestType, owner_cpf = "XXXXXXXXXXX"):
        self.__owner_student_cpf : str = owner_cpf
        self.__test_type : TestType = test_type
        self.answers = None

    def update_answers(self, questions : list[Question]) -> None:
        for question in questions:
            self.answers[question.number - 1] = question.answer

    def set_owner_cpf(self, cpf : str) -> None:
        self.__owner_student_cpf = cpf
    
    def get_owner_cpf(self) -> str:
        return self.__owner_student_cpf
    
    def get_test_type(self) -> TestType:
        return self.__test_type
    
    def get_answers(self) -> list[AlphaAnswer | NumericAnswer | BinaryAnswer]:
        return self.answers


class PsQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.PS, **kwargs)
        self.questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 61)]


class SimulinhoQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMULINHO, **kwargs)
        self.questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 51)]


class SimufscQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUFSC, **kwargs)
        self.questions : list[NumericAnswer] = [NumericAnswer() for _ in range(1, 51)]


class SimuenemQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUENEM, **kwargs)
        self.questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 181)]
