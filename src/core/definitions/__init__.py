__all__ = ['PLATAFORM', 'PATH_SEPARATOR', 'Stage', 'TestType', 'Subject']


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
