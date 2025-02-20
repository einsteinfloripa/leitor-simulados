from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from api import CoreApi

from core.definitions.test_defs import TestType
from core.definitions.question import TestQuestions
from core.definitions.blocks import TestBlocks
from core.builder import Builder

from api.data_structs import ImageCacheStruct



class BuilderApi:
    """
    Class responsible for the communication between the api and the core builder.

    Attributes:
    - coreApi : CoreApi
        The core api object.
    - test_type : TestType
        The type of test that will be resolved.
    - builder : Builder
        The builder object that will resolve the test.
    """
    
    def __init__(self, coreApi : CoreApi, test_type : TestType):
        self.coreApi : CoreApi = coreApi
        self.test_type : TestType = test_type
        self.builder : Builder = Builder.from_test_type(test_type)


    def resolve_from_cache(self, index : int) -> TestQuestions:
        """
        This function resolves the answers of the test from the cache and
        stores the results in the cache.
        
        Arguments:
        - index : int
            The index of the cache to resolve.
        """
        # Get the cache
        cache : ImageCacheStruct | None = self.coreApi.cache.from_index(index)
        blocks : TestBlocks = cache.blocks
        # Build the result
        result = self.resolve_test(blocks)
        # Cache the detections
        cache.questions = result
        return result


    def resolve_test(self, test_blocks : TestBlocks) -> TestQuestions:
        """
        Gives the answers of the whole test, including the CPF value.
        
        Arguments:
        - test_blocks : TestBlocks
            TestBlocks object conteining the information of the test.
        """
        # Create the report object
        report = TestQuestions.from_test_type(self.test_type)
        # Get the answers from de builder
        report.set_owner_cpf(self.builder.resolve_cpf(test_blocks.cpf_block))
        for block in test_blocks.questions_blocks:
            report.update_answers(self.builder.resolve_question_block(block))
        # Cache the detections
        return report
        








