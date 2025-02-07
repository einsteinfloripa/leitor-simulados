from __future__ import annotations
from enum import Enum
from typing import Type

from dataclasses import dataclass

from definitions import TestType
from definitions.geometry import IntPoint

class AlphaAnswer(Enum):
    NOT_ANSWERED = -1
    NULL = 0
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5

class BinaryAnswer(Enum):
    NOT_ANSWERED = -1
    NULL = 0
    TRUE = 1
    FALSE = 2

class NumericAnswer:
    NOT_ANSWERD = -1
    NULL = 0

    def __init__(self, value : int = -1):
        if value == -1: self.set_null()
        elif value == 0: self.set_not_answered()
        else: self.set(value)

    def set(self, value: int):
        if not isinstance(value, int):
            raise ValueError("Numeric answer must be an integer.")
        if value < -1:
            raise ValueError("Numeric answer must be non-negative.")
        if value > 99:
            raise ValueError("Numeric answer must be less than 100.")
        self.value = value

@dataclass
class Question:
    """
    Base question class, used to store the number and answer of a question.
    """
    number : int
    answer : AlphaAnswer | NumericAnswer | BinaryAnswer | None = None
    position : IntPoint | None = None

    def __repr__(self):
        return f'{self.number}: {self.answer}'


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
        if test_type == TestType.PS_ALUNOS:
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
        self._owner_student_cpf : str = owner_cpf
        self._test_type : TestType = test_type
        self._questions : list[AlphaAnswer | NumericAnswer | BinaryAnswer] = []

    def update_answers(self, questions : list[Question]) -> None:
        for question in questions:
            self._questions[question.number - 1] = question

    def set_owner_cpf(self, cpf : str) -> None:
        self._owner_student_cpf = cpf
    
    def get_owner_cpf(self) -> str:
        return self._owner_student_cpf
    
    def get_test_type(self) -> TestType:
        return self._test_type
    
    def get_questions(self) -> list[AlphaAnswer | NumericAnswer | BinaryAnswer]:
        return self._questions


class PsQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.PS_ALUNOS, **kwargs)
        self._questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 61)]


class SimulinhoQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMULINHO, **kwargs)
        self._questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 51)]


class SimufscQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUFSC, **kwargs)
        self._questions : list[NumericAnswer] = [NumericAnswer() for _ in range(1, 51)]


class SimuenemQuestions(TestQuestions):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUENEM, **kwargs)
        self._questions : list[AlphaAnswer] = [AlphaAnswer.NULL for _ in range(1, 181)]
