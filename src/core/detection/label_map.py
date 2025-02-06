from __future__ import annotations

from dataclasses import dataclass

from definitions import Stage
from . import Detection

## Label maps ##
@dataclass
class LabelMap:

    detections : list[Detection.Type]
    stage : Stage


## Default Label Maps ##
DEFAULT_FIRST_STAGE_LABEL_MAP = LabelMap(
    detections = [
        Detection.Type.CPF_BLOCK,
        Detection.Type.QUESTION_BLOCK,
    ],
    stage = Stage.FIRST
)

DEFAULT_SECOND_STAGE_LABEL_MAP = LabelMap(
    detections = [
        Detection.Type.CPF_COLUMN,
        Detection.Type.QUESTION_LINE,
        Detection.Type.SELECTED_BALL,
        Detection.Type.UNSELECTED_BALL,
        Detection.Type.QUESTION_NUMBER,
        Detection.Type.QUESTION_COLUMN,
    ],
    stage = Stage.SECOND
)

        