from __future__ import annotations

from definitions import TestType, Subject
from definitions.question import (
    AlphaAnswer,
    BinaryAnswer,
    NumericAnswer,
)



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
