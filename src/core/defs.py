from enum import Enum
import platform

# Constants
PLATAFORM = platform.system()
PATH_SEPARATOR = '\\' if PLATAFORM == 'Windows' else '/'

# Type classes
class Stage(Enum):
    NULL = 0
    FIRST = 1
    SECOND = 2
    BOTH = 3

class TestType(Enum):
    NULL = 0
    PS = 1
    SIMULINHO = 2
    SIMUFSC = 3
    SIMUENEM = 4