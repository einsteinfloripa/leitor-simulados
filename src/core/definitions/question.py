from __future__ import annotations
from enum import Enum
from typing import Type

from dataclasses import dataclass

from core.definitions import TestType
from core.definitions.geometry import IntPoint


# SECTION: Answer types

class AlphaAnswer(Enum):
    NULL = -1
    NOT_ANSWERED = 0
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5

class BinaryAnswer(Enum):
    NULL = -1
    NOT_ANSWERED = 0
    TRUE = 1
    FALSE = 2

class NumericAnswer:
    NULL = -1
    NOT_ANSWERD = 0

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
        self.name = str(value)
    
    def set_null(self):
        self.value = -1
        self.name = "NULL"

    def set_not_answered(self):
        self.value = 0
        self.name = "NOT_ANSWERED"



# SECTION: Question class

@dataclass
class Question:
    """
    Base question class, used to store the number and answer of a question.
    """
    number : int
    answer : AlphaAnswer | NumericAnswer | BinaryAnswer | None = None
    position : IntPoint | None = None
    updated : bool = False

    def __repr__(self):
        return f'{self.number}: {self.answer}'



# SECTION: Question container class

class TestReport:
    """
    This class is responsable for storing the answers of a test.
    """

    @classmethod
    def from_test_type(
            cls,
            test_type : TestType,
            owner_cpf : str = "XXXXXXXXXXX"
        ) -> Type[TestReport]:
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
        # CPF
        self._owner_student_cpf : str = owner_cpf
        self._cpf_updated : bool = False
        # Test variables
        self._test_type : TestType = test_type
        self._questions : list[Question] = []

    def update_answer(self, question : Question, updated=False) -> None:
        self._questions[question.number - 1].answer = question.answer
        question.updated = updated
    
    def update_answers(self, questions : list[Question], updated=False) -> None:
        for question in questions:
            self._questions[question.number - 1] = question
            question.updated = updated

    def set_owner_cpf(self, cpf : str, updated=False) -> None:
        self._owner_student_cpf = cpf
        self._cpf_updated = updated
    
    def get_owner_cpf(self) -> str:
        return self._owner_student_cpf
    
    def get_test_type(self) -> TestType:
        return self._test_type
    
    def get_questions(self) -> list[AlphaAnswer | NumericAnswer | BinaryAnswer]:
        return self._questions
    
    def get_cpf_updated(self) -> bool:
        return self._cpf_updated
    
    def to_dict(self) -> list:
        d = {
            'owner_cpf': self._owner_student_cpf,
            **{ f"{q.number:02}" : q.answer.name for q in self._questions }
        }
        return d


class PsQuestions(TestReport):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.PS_ALUNOS, **kwargs)
        self._questions : list[Question] = [
            Question(number,AlphaAnswer.NULL,None,False) for number in range(1, 61)
        ]


class SimulinhoQuestions(TestReport):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMULINHO, **kwargs)
        self._questions : list[Question] = [
            AlphaAnswer.NULL for _ in range(1, 51)
        ]


class SimufscQuestions(TestReport):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUFSC, **kwargs)
        self._questions : list[Question] = [
            Question(number,NumericAnswer(),None,False) for number in range(1, 61)    
        ]


class SimuenemQuestions(TestReport):
    def __init__(self, **kwargs) -> None:
        super().__init__(TestType.SIMUENEM, **kwargs)
        self._questions : list[Question] = [
            Question(number,AlphaAnswer.NULL,None,False) for number in range(1, 181)
        ]
