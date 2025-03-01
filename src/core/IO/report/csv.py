from pathlib import Path
import csv

from core.IO import FileExtension
from core.IO.report import (
    ReportIO,
    ReportData,
) 

from core.definitions import TestType
from core.definitions.question import (
    Question,
    AlphaAnswer,
    NumericAnswer
)

class DefaultCSV(ReportIO):

    @property
    def extension(self) -> FileExtension:
        return FileExtension.CSV

    @ReportIO.assert_data
    def write(self, data: ReportData, fullpath : Path) -> None:
        
        # Create header list
        header = _get_header(data.test_type)
        config_dict : dict = self.get_config()['config']
        config_header = config_dict.keys()
        header = list(config_header) + header
        
        # Iterate over the data making the data lists
        config_values = list(config_dict.values())
        output_data = []
        for name, test_questions in zip(data.names, data.test_questions):

            # Cpf
            student_data = config_values + [test_questions.get_owner_cpf()]
            
            # Answers
            questions : list[Question] = test_questions.get_questions()
            for question in questions:
                number : int = question.number
                answer : AlphaAnswer | NumericAnswer = question.answer
                txt_answer : str = answer.name\
                    if isinstance(answer, AlphaAnswer) else str(answer.value)
                student_data.append(txt_answer)
            output_data.append(student_data)
        
        # Write the output to a csv file
        with open(fullpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for student_data in output_data:
                writer.writerow(student_data)


def _get_header(test_type: TestType) -> list[str]:
    if test_type == TestType.PS_ALUNOS:
        return ['owner_cpf'] + [str(i) for i in range(1, 61)]
    elif test_type == TestType.SIMULINHO:
        return ['owner_cpf'] + [str(i) for i in range(1, 51)]
    elif test_type == TestType.SIMUENEM:
        return ['owner_cpf'] + [str(i) for i in range(1, 181)]
    else:
        raise NotImplementedError(f"Test type {test_type} not implemented")
            
