from __future__ import annotations

import cv2

from dataclasses import dataclass
from pathlib import Path

from core.definitions.question import TestReport, Question

from utils.log import LoggingSystem

from ..base import Exporter, Importer
from .. import FileExtension


@dataclass
class ImageReportExportData:
    images: list[str]
    reports: list[TestReport]

    def unpack(self):
        return zip(self.images, self.reports)



class ImageReportExporter(Exporter):

    _logger = LoggingSystem.get_new_logger("ImageReportExporter")

    @property
    def extension(self):
        return FileExtension.IMAGETYPE
    
    @Exporter.folder_export
    def export(
            self,
            out_dir : Path,
            data : ImageReportExportData,
        ) -> bool:
        """
        Export the images with detections to a selected folder.

        Parameters
        ----------
        event : any
            The event that triggered the export action.
        """
        # Base font values
        base_image_height = 1800
        
        for img_path, report in data.unpack():
            # Logging
            if report is None:
                self._logger.warning(f"Skipping image {img_path} with no report")
                continue
            self._logger.info(f"Exporting image {img_path} with report {report}")

            # Load the image
            img_raw = Importer.load_cv2_image(img_path)
            
            height, width, _ = img_raw.shape
            font_scale =  height / base_image_height

            # Get the questions
            # No need to specify the index since the image is already selected
            questions: list[Question] = report.get_questions()
            for question in questions:
                if question.position is None:
                    continue
                x, y = question.position
                # Offset to ajust the text position
                x = x - int(width*0.05)

                if question.answer.value == 0:
                    text = "BRANCO"
                elif question.answer.value == -1:
                    text = "NAO DETECTADO"
                else:
                    text = f"{question.number} : {question.answer.name}"

                color = (92, 92, 200) if not question.updated else (0, 129, 255)
                
                #logging
                self._logger.debug(f'Drawing QUESTION_BLOCK text "{text}" at position "({x}, {y})" \
with color "{color}" and font scale "{font_scale}"')
                cv2.putText(
                    img_raw,
                    text,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    3,
                    cv2.LINE_AA,
                )

            # Get the cpf
            cpf = report.get_owner_cpf()
            updated = report.get_cpf_updated()
            text = f"CPF: {cpf}"

            x = int(width * 0.6)
            y = int(height * 0.3)
            
            color = (92, 92, 200) if not updated else (0, 129, 255)
            # Logging
            self._logger.debug(f'Drawing CPF_BLOCK text "{text}" at position "({x}, {y})" \
with color "{color}" and font scale "{font_scale}"')
            cv2.putText(
                    img_raw,
                    text,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    3,
                    cv2.LINE_AA,
                )
            out_path = str(out_dir / Path(img_path).name)

            self._logger.debug(f"Saving image to: {out_path}")
            cv2.imwrite(out_path, img_raw)
        
        return True