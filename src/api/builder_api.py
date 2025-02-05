from api import CoreApi
from core.builder.data_structs import Block, TestBlocks
from core.builder import Builder
from definitions.test_defs import (
    Question,
    TestAnswers,
    TestType
)


class BuilderApi:
    """
    Class that operates on Blocks to build the answer of each question.
    """
    
    def bind_builder(self, test_type : TestType):
        self.test_type = test_type
        self.builder = Builder.from_test_type(test_type)

    def resolve_Test(self, test_blocks : TestBlocks) -> TestAnswers:
        """
        Gives the answers of the whole test, including the CPF value.
        """
        test_answers = TestAnswers.from_test_type(self.test_type)
        # Get the CPF value
        test_answers.cpf = self.resolve_cpf_block(test_blocks.cpf_block)
        # Get the questions values


    def resolve_cpf_block(self, cpf_block : Block) -> str:
        return self.builder.resolve_cpf(cpf_block)

        

    def resolve_question_block(self, block : Block) -> list[Question]:
        return self.builder.resolve_question_block(block)







