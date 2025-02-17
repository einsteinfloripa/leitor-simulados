from __future__ import annotations
from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from .api import CoreApi


from pathlib import Path
import cv2

from core.definitions import Stage, TestType, PATH_SEPARATOR
from core.model import load_model
from core.image import CoreImage
from core.IO import Importer, FileExtension, Exporter
from core.IO.report import ReportIO, ReportData
from core.IO.detection.export_yolo import DetectionsExportData, YOLOExporter

from .data_structs import ImageCacheStruct


# SECTION: IOApi class

class IOApi:

    ## Initialization ##
    def __init__(self, core : CoreApi):
        self.core  = core



    # SECTION: Input Output Methods


    ## Import Methods ##

    def open_folder(self, folder_path : str) -> bool:
        files = Importer.Find.image_files(folder_path)
        if files:
            # Save the image paths
            self.core.set_image_files(files)
            # Set the cache list
            number_of_images = len(files)
            self.core.set_number_of_images(number_of_images)
            self.core.set_cache(number_of_images)
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
            self.core.set_fs_model(model)
        else:
            self.core.set_ss_model(model)
        return True


    ## Export Methods ##

    # Report Export

    def save_report(
            self,
            test_type : TestType,
            fullpath : str,
            exporter_name : str = "DefaultJSON",
        ):
        # Get the exporter
        exporter : ReportIO = ReportIO.get_by_name(exporter_name)
        
        # Get the data
        data : list[ImageCacheStruct] = self.core.cache.get_all()
        
        # Format the data for saving
        formated_data : ReportData = ReportData(
            test_type=test_type,
        )
        for img_cache in data:
            if img_cache:
                formated_data.names.append(img_cache.img_name)
                formated_data.test_questions.append(img_cache.questions)
        
        # Call the exporter
        exporter.write(formated_data, fullpath=fullpath)


    # Detection Export
    
    def export_yolo(
            self,
            fullpath : str,
            save_images : bool = False
        ) -> bool:
        
        # Get the data
        cache = self.core.cache
        data : list[ImageCacheStruct] = cache.get_all()
        formated_data : DetectionsExportData = DetectionsExportData(
            names = [],
            test_blocks = []
        )

        # Format the data for saving
        for img_cache in data:
            if img_cache:
                formated_data.names.append(img_cache.img_name)
                formated_data.test_blocks.append(img_cache.blocks)

        # Call the exporter
        exporter = YOLOExporter()
        success = exporter.export(formated_data, fullpath=fullpath)
        
        # Save the images if needed
        dest = []
        imgs : Generator[CoreImage, None, None] = CoreImage.from_paths(
            self.core.get_image_files()
        )
        if success and save_images:
            for name in formated_data.names:
                out_folder = fullpath + PATH_SEPARATOR + name.split('.')[0]
                dest.append(out_folder)
        Exporter.save_images(dest, imgs)

        return success



    # SECTION: Getters && Setters
    
    def get_report_output_formats(self) -> list[(str, FileExtension)]:
        return ReportIO.get_available_formats()


    
    # SECTION: Auxiliar Methods

    def load_image(self, index : int) -> bool:
        img = CoreImage.from_path(self.core.get_image_files()[index])
        self.core.set_image(img)
        self.core.set_rbg_image_raw(
            cv2.cvtColor(img.raw, cv2.COLOR_BGR2RGB)
        )
        return True
        


