# imports

import math

from core.definitions.enums import Stage
from core.detection.base import Detection
from core.image import CoreImage
from core.definitions.geometry import FloatBoundingBox, Axis, Line
from core.IO import MODELS_PATH

from EFScanAlgoCore.scanner import Scanner, Context
from EFScanAlgoCore.ef_utils import ef_get_tilt


# Target stage definition
TARGET_STAGE = Stage.FIRST # or Stage.SECOND or Stage.BOTH

# Model initalization function [OPTIONAL] ( runs once at the loading time )
def init_pipeline(scanner : Scanner) -> None:
    # set a variable to be used in the detect function
    scanner.exemple = Exemple().get_meaningfull_variable()

# Main detect fucntion ( runs once for each image )
def detect(scanner : Scanner, img : CoreImage) -> list[Detection]:
    print(scanner.exemple)
    return []

# Other aux class/fucntion functions [OPTIONAL] ... 
class Exemple:
    def get_meaningfull_variable(self):
        return 42