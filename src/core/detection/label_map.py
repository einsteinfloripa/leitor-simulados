from __future__ import annotations

from dataclasses import dataclass

from core.definitions import Stage
from . import Detection

## Label maps ##
@dataclass
class LabelMap:

    @classmethod
    def from_json(cls, json_dict : dict) -> LabelMap:
        """
        Create a LabelMap from a JSON dictionary
        """
        if not json_dict:
            return None
        return cls(
            detections = [Detection.Type[detection] for detection in json_dict['values']],
            stage = Stage[json_dict['stage']]
        )

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
        Detection.Type.SELECTED_BALL,
        Detection.Type.UNSELECTED_BALL,
    ],
    stage = Stage.SECOND
)

        