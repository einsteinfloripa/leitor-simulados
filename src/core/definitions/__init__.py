"""
Core definitions package.

This package provides the fundamental definitions used throughout the project, such as
enumerations, geometry types, block and question representations, and test-specific constants.
"""

__all__ = [
    # Enumerations
    "Stage", "TestType", "Subject",
    # Geometry types
    "Axis", "Line", "IntPoint", "FloatPoint", "FloatBoundingBox", "IntBoundingBox",
    # Blocks and test structure
    "Block", "TestBlocks",
    # Answer types
    "AlphaAnswer", "BinaryAnswer", "NumericAnswer",
    # Questions
    "Question", "TestQuestions", "PsQuestions", "SimulinhoQuestions", "SimufscQuestions", "SimuenemQuestions",
    # Test-specific definitions
    "PsAlunosDefinitions", "SimulinhoDefinitions", "SimufscDefinitions", "SimuenemDefinitions"
]

# Enumerations
from .enums import Stage, TestType, Subject

# Geometry types
from .geometry import (
    Axis,
    Line,
    IntPoint,
    FloatPoint,
    FloatBoundingBox,
    IntBoundingBox
)

# Blocks
from .blocks import Block, TestBlocks

# Questions
from .question import (
    Question,
    TestQuestions,
    PsQuestions,
    SimulinhoQuestions,
    SimufscQuestions,
    SimuenemQuestions
)

# Test-specific definitions
from .test_defs import (
    PsAlunosDefinitions,
    SimulinhoDefinitions,
    SimufscDefinitions,
    SimuenemDefinitions
)

