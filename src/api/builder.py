from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from api import CoreApi


from api.data_structs import ImageCacheStruct

from core.builder.data_structs import TestBlocks
from core.builder import Builder
from definitions.test_defs import TestType
from definitions.question import TestQuestions


class BuilderApi:
    """
    Class that operates on Blocks to build the answer of each question.
    """
    
    def __init__(self, coreApi : CoreApi, test_type : TestType):
        self.coreApi = coreApi
        self.test_type = test_type
        self.builder = Builder.from_test_type(test_type)

    def resolve_from_cache(self, index : int) -> TestQuestions:
        """
        This function resolves the answers of the test from the cache and
        stores the results in the cache.
        """
        # Get the cache
        cache : ImageCacheStruct | None = self.coreApi.get_cache().from_index(index)
        blocks : TestBlocks = cache.blocks
        # Build the result
        result = self.resolve_test(blocks)
        # Cache the detections
        cache.questions = result
        return result

    def resolve_test(self, test_blocks : TestBlocks) -> TestQuestions:
        """
        Gives the answers of the whole test, including the CPF value.
        """
        # Create the report object
        report = TestQuestions.from_test_type(self.test_type)
        # Get the answers from de builder
        report.set_owner_cpf(self.builder.resolve_cpf(test_blocks.cpf_block))
        for block in test_blocks.questions_blocks:
            report.update_answers(self.builder.resolve_question_block(block))
        # Cache the detections
        return report
        








