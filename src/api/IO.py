from __future__ import annotations
from typing import TYPE_CHECKING, Generator, Optional
if TYPE_CHECKING:
    from .api import CoreApi

from pathlib import Path
import cv2

from core.definitions import Stage, TestType
from core.model import load_model
from core.image import CoreImage
from core.IO import Importer, FileExtension
from core.IO.report import ReportIO, ReportData
from core.IO.detection.export_yolo import DetectionsExportData, YOLOExporter

from .data_structs import ImageCacheStruct

class IOApi:
    """
    Handles input and output operations for CoreApi, including importing images,
    loading models, and exporting reports and detection results.
    """
    
    def __init__(self, core: CoreApi):
        """
        Initializes the IOApi with a reference to the CoreApi instance.

        Parameters
        ----------
        core : CoreApi
            The core API instance.
        """
        self.core = core

    def open_folder(self, folder_path: str) -> bool:
        """
        Opens a folder and loads image file paths into CoreApi.

        Parameters
        ----------
        folder_path : str
            Path to the folder containing image files.

        Returns
        -------
        bool
            True if images were found and loaded, False otherwise.
        """
        files = Importer.Find.image_files(folder_path)
        if files:
            self.core.image_files = files
            self.core.number_of_images = len(files)
            self.core.reset_cache(len(files))
            return True
        return False

    def load_model(self, model_path: str, stage: Stage = Stage.NULL) -> bool:
        """
        Loads a detection model and assigns it to the corresponding stage.

        Parameters
        ----------
        model_path : str
            Path to the model file.
        stage : Stage, optional
            The stage of the model (first or second), by default Stage.NULL.

        Returns
        -------
        bool
            True if the model was successfully loaded, False otherwise.
        """
        model = load_model(model_path, stage)
        if not model:
            return False
        if stage == Stage.FIRST:
            self.core.fs_model = model
        else:
            self.core.ss_model = model
        return True

    def save_report(self, test_type: TestType, fullpath: Path, exporter_name: str = "DefaultJSON"):
        """
        Saves a report using the specified exporter.

        Parameters
        ----------
        test_type : TestType
            The type of test used for the report.
        fullpath : Path
            The full path where the report should be saved.
        exporter_name : str, optional
            Name of the exporter to use, by default "DefaultJSON".
        """
        exporter: ReportIO = ReportIO.get_by_name(exporter_name)
        data: list[ImageCacheStruct] = self.core.cache.get_all()
        formatted_data = ReportData(test_type=test_type)
        
        for img_cache in data:
            if img_cache:
                formatted_data.names.append(img_cache.img_name)
                formatted_data.test_questions.append(img_cache.questions)
        
        exporter.write(formatted_data, fullpath)

    def export_yolo(self, fullpath: str | Path, save_images: bool = False) -> bool:
        """
        Exports detection results in YOLO format.

        Parameters
        ----------
        fullpath : str | Path
            The path where the YOLO format data should be saved.
        save_images : bool, optional
            Whether to save the associated images, by default False.

        Returns
        -------
        bool
            True if export was successful, False otherwise.
        """
        fullpath = Path(fullpath) if isinstance(fullpath, str) else fullpath
        data: list[ImageCacheStruct] = self.core.cache.get_all()
        formatted_data = DetectionsExportData(names=[], test_blocks=[])
        
        for img_cache in data:
            if img_cache:
                formatted_data.names.append(img_cache.img_name)
                formatted_data.test_blocks.append(img_cache.blocks)
        
        imgs: Optional[Generator[CoreImage, None, None]] = (
        CoreImage.from_paths(self.core.image_files, lazy=True) if save_images else None
        )
        exporter = YOLOExporter()
        return exporter.export(fullpath, formatted_data, imgs=imgs)

    def get_report_output_formats(self) -> list[tuple[str, FileExtension]]:
        """
        Retrieves available report output formats.

        Returns
        -------
        list[tuple[str, FileExtension]]
            A list of available report formats.
        """
        return ReportIO.get_available_formats()

    def load_image(self, index: int) -> bool:
        """
        Loads an image at the specified index and updates CoreApi.

        Parameters
        ----------
        index : int
            The index of the image to load.

        Returns
        -------
        bool
            True if the image was successfully loaded, False otherwise.
        """
        img = CoreImage.from_path(self.core.image_files[index])
        self.core.image = img
        self.core.rgb_image_raw = cv2.cvtColor(img.raw, cv2.COLOR_BGR2RGB)
        return True
