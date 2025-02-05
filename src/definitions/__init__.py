import platform
from enum import Enum

# Sys constants
PLATAFORM = platform.system()
PATH_SEPARATOR = '\\' if PLATAFORM == 'Windows' else '/'

class Stage(Enum):
    NULL = 0
    FIRST = 1
    SECOND = 2
    BOTH = 3

from definitions.question import (
    AlphaAnswer,
    BinaryAnswer,
    NumericAnswer,
    Question,
    TestQuestions
)

from definitions.test_defs import (
    TestType,
    Subject,
    PsAlunosDefinitions,
    SimulinhoDefinitions,
    SimufscDefinitions,
    SimuenemDefinitions,
)