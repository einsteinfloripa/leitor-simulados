from dataclasses import dataclass, field
from core.detection import Detection
from utils.data_classes import FloatBoundingBox

@dataclass
class Block:
    """
    Represents a block of questions or CPF tha had smaller detections inside.

    Attributes:
    - root_detection: The type of the detection that represents the block.
    - order: The order of the block in the test (0 is the top left most block).
    - detections: A dict with the position of the detections inside the block sorted
    by type.
    """
    root_detection: Detection.Type = field(default=Detection.Type.NULL)
    order: int = field(default=None)
    detections: dict[Detection.Type, FloatBoundingBox] = field(default_factory=list)


@dataclass
class TestBlocks:
    """
    Represents on test (i.e. the answers of one student).

    Attributes:
    - name: The name of the test image.
    - cpf_block: The block that represents the CPF of the student.
    - questions_block: A list of blocks that represents the questions of the test.
    """
    name: str = field(default='')
    cpf_block: Block = field(default=None)
    questions_block: list[Block] = field(default_factory=list)
