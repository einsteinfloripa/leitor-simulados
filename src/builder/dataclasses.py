from __future__ import annotations

from dataclasses import dataclass,field

@dataclass
class Block():
    name: str = field(default='')
    order: int = field(default=None)
    detections: list[dict] = field(default_factory=list)

@dataclass
class BuilderContext:
    name: str = field(default='')
    cpf_block: Block = field(default=None)
    questions_block: list[dict] = field(default_factory=list)