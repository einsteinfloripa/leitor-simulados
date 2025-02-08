from dataclasses import dataclass, field
from core.detection import DetectionContainer, Detection

@dataclass
class Block:
    """
    Represents a block of questions or CPF tha had smaller detections inside.

    Attributes:
    - root_detection: The type of the detection that represents the block.
    - order: The order of the block in the test (0 is the top left most block).
    - detections: Contains the detections inside of the block.
    """
    root_detection : Detection = field(default=None)
    order: int = field(default=None)
    container: DetectionContainer = field(default=None)


@dataclass
class TestBlocks:
    """
    Represents on test (i.e. the answers of one student).

    Attributes:
    - name: The name of the test image.
    - cpf_block: The block that represents the CPF of the student.
    - questions_blocks: A list of blocks that represents the questions of the test.
    """
    name: str = field(default='')
    cpf_block: Block = field(default=None)
    questions_blocks: list[Block] = field(default_factory=list)
