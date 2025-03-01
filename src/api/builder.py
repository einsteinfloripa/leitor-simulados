from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from api import CoreApi

from core.definitions.test_defs import TestType
from core.definitions.question import TestQuestions
from core.definitions.blocks import TestBlocks
from core.builder import Builder
from api.data_structs import ImageCacheStruct


class BuilderApi:
    """
    Handles communication between the API and the core builder for test resolution.

    Attributes
    ----------
    coreApi : CoreApi
        The core API instance.
    test_type : TestType
        The type of test to be resolved.
    builder : Builder
        The builder instance responsible for resolving test questions.
    """

    def __init__(self, coreApi: CoreApi, test_type: TestType):
        """
        Initializes the Builder API.

        Parameters
        ----------
        coreApi : CoreApi
            The core API instance.
        test_type : TestType
            The test type to be resolved.
        """
        self.coreApi: CoreApi = coreApi
        self.test_type: TestType = test_type
        self.builder: Builder = Builder.from_test_type(test_type)

    def resolve_from_cache(self, index: int) -> Optional[TestQuestions]:
        """
        Resolves test answers from the cache and updates the cached data.

        Parameters
        ----------
        index : int
            The index of the cached test data to resolve.

        Returns
        -------
        Optional[TestQuestions]
            The resolved test questions if cache data exists, otherwise None.
        """
        # Retrieve cached data
        cache: Optional[ImageCacheStruct] = self.coreApi.cache.from_index(index)
        if cache is None:
            return None

        blocks: TestBlocks = cache.blocks
        # Resolve test questions
        result = self.resolve_test(blocks)
        # Update cache with resolved questions
        cache.questions = result
        return result

    def resolve_test(self, test_blocks: TestBlocks) -> TestQuestions:
        """
        Computes answers for the test, including the CPF value.

        Parameters
        ----------
        test_blocks : TestBlocks
            The structured test blocks containing the test data.

        Returns
        -------
        TestQuestions
            The resolved test questions.
        """
        # Initialize the test report
        report = TestQuestions.from_test_type(self.test_type)

        # Resolve the CPF owner
        report.set_owner_cpf(self.builder.resolve_cpf(test_blocks.cpf_block))

        # Process each question block
        for block in test_blocks.questions_blocks:
            report.update_answers(self.builder.resolve_question_block(block))

        return report
