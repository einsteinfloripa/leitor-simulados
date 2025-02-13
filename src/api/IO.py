from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .api import CoreApi


from pathlib import Path
import cv2

from definitions import Stage, TestType
from core.model import load_model
from core.image import Image
from core.IO import Importer, FileExtension
from core.IO.report import ReportIO, ReportData

from .data_structs import ImageCacheStruct


# SECTION: IOApi class

class IOApi:

    ## Initialization ##
    def __init__(self, core : CoreApi):
        self._core  = core


    # SECTION: Input Output Methods

    def open_folder(self, folder_path : str) -> bool:
        files = Importer.Find.image_files(folder_path)
        if files:
            # Save the image paths
            self._core.set_image_files(files)
            # Set the cache list
            number_of_images = len(files)
            self._core.set_number_of_images(number_of_images)
            self._core.set_cache(number_of_images)
            return True
        return False

    def load_model(
            self,
            model_path : str,
            stage : Stage = Stage.NULL
            ) -> bool:
        model = load_model(model_path, stage)
        if not model:
            return False
        if stage == Stage.FIRST:
            self._core.set_fs_model(model)
        else:
            self._core.set_ss_model(model)
        return True

    def save_report(
            self,
            test_type : TestType,
            fullpath : str | Path,
            exporter_name : str = "DefaultJSON",
        ):
        # Convert the file_path to a Path object if needed
        # Get the exporter
        cache = self._core.get_cache()
        exporter : ReportIO = ReportIO.get_by_name(exporter_name)
        # Get the data
        data : list[ImageCacheStruct] = cache.get_all()
        # Format the data for saving
        formated_data : ReportData = ReportData(
            test_type=test_type,
        )
        for img_cache in data:
            formated_data.names.append(img_cache.img_name)
            formated_data.test_questions.append(img_cache.questions)        
        # Call the exporter
        exporter.write(formated_data, fullpath=fullpath)



    # SECTION: Getters && Setters
    
    def get_report_output_formats(self) -> list[(str, FileExtension)]:
        return ReportIO.get_available_formats()
    
    # SECTION: Auxiliar Methods

    def load_image(self, index : int) -> bool:
        img = Image.from_path(self._core.get_image_files()[index])
        self._core.set_image(img)
        self._core.set_rbg_image_raw(
            cv2.cvtColor(img.raw, cv2.COLOR_BGR2RGB)
        )
        return True
        


