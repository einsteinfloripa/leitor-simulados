from __future__ import annotations

from pathlib import Path
import json

from core.IO import FileExtension
from core.IO.report import (
    ReportIO,
    ReportData,
) 

from core.definitions.question import (
    Question,
    AlphaAnswer,
    NumericAnswer
)

__all__ = ['DefaultJSON']

class DefaultJSON(ReportIO):

    @property
    def extension(self) -> FileExtension:
        return FileExtension.JSON

    def write(self, data: ReportData, fullpath : Path) -> None:

        # Create the output dictionary
        output_dict = {'data': {}}
        output_dict.update(self.get_config())
        
        # Iterate over the data
        for name, test_report in zip(data.names, data.test_reports):

            # Create the student output
            student_output = {}
            student_output['owner_cpf'] = test_report.get_owner_cpf()
            questions : list[Question] = test_report.get_questions()
            for question in questions:
                number : int = question.number
                answer : AlphaAnswer | NumericAnswer = question.answer
                txt_answer : str = answer.name\
                    if isinstance(answer, AlphaAnswer) else str(answer.value)
                student_output[str(number)] = txt_answer
            output_dict['data'][name] = student_output
        
        # Write the output to a json file
        with open(fullpath, 'w') as f:
            json.dump(output_dict, f, indent=4)


            
