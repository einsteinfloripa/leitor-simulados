from __future__ import annotations

from enum import Enum

from dataclasses import dataclass, field
from typing import Type
from definitions.question import (
    AlphaAnswer,
    BinaryAnswer,
    NumericAnswer,
)


class TestType(Enum):
    NULL = 0
    PS_ALUNOS = 1
    SIMULINHO = 2
    SIMUFSC = 3
    SIMUENEM = 4

class Subject(Enum):
    MATH = 0
    PHYSICS = 1
    CHEMISTRY = 2
    BIOLOGY = 3
    HISTORY = 4


# The folowing classes are used to store constant definitions for each test type
class PsAlunosDefinitions:
    TEST_TYPE : TestType = TestType.PS_ALUNOS
    
    SUBJECTS : list[Subject] = "TO_BE_DEFINED"
    ANSWER_TYPES : AlphaAnswer | BinaryAnswer | NumericAnswer = AlphaAnswer 
    NUM_QUESTIONS_PER_SUBJECT : int = "TO_BE_DEFINED"
    
    NUM_QUESTIONS : int = 60
    NUM_BLOCKS : int = 6
    NUM_BLOCK_PER_ROW : int = 3
    NUM_BLOCKS_PER_COLUMN : int = 2
    NUM_QUESTIONS_PER_BLOCK : int = 10


class SimulinhoDefinitions:
    pass

class SimufscDefinitions:
    pass

class SimuenemDefinitions:
    pass
