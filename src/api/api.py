from __future__ import annotations
from typing import Generator, Optional
from pathlib import Path

import numpy as np
import cv2

from core.image import CoreImage
from core.model import DetectionModel, load_model
from core.definitions import TestType, Stage
from core.IO import Importer, FileExtension
from core.IO.report import ReportIO, ReportData
from core.IO.detection.export_yolo import DetectionsExportData, YOLOExporter

from .data_structs import ImageCacheStruct
from .caching import Cache
from .builder import BuilderApi
from .IO import IOApi


class CoreApi:
    """
    Core API class responsible for managing images, caching, and models.
    """
    
    def __init__(self):
        """
        Initializes the CoreApi with default values and helper components.
        """
        # CoreImage
        self.__image: Optional[CoreImage] = None
        self.__rgb_image_raw: Optional[np.ndarray] = None

        # Helpers
        self.__cache: Cache = Cache(0)
        self.__builder: Optional[BuilderApi] = None

        # Context Variables
        self.__image_files: Optional[list[str]] = None
        self.__number_of_images: Optional[int] = None
        self.__fs_model: Optional[DetectionModel] = None
        self.__ss_model: Optional[DetectionModel] = None
        self.__current_set_index: Optional[int] = None
        self.__current_test_type: Optional[TestType] = None
        
        # Internal only
        self.__last_builder_type: TestType = TestType.NULL


# =============================================================================
# Properties
# =============================================================================


    @property
    def image(self) -> Optional[CoreImage]:
        """
        Get the currently loaded CoreImage instance.

        Returns
        -------
        Optional[CoreImage]
            The current CoreImage instance, if available.
        """
        return self.__image

    @image.setter
    def image(self, image: CoreImage):
        """
        Set the CoreImage instance.

        Parameters
        ----------
        image : CoreImage
            The CoreImage instance to set.

        Raises
        ------
        TypeError
            If the provided image is not an instance of CoreImage.
        """
        if not isinstance(image, CoreImage):
            raise TypeError("image must be an instance of CoreImage")
        self.__image = image

    @property
    def rgb_image_raw(self) -> Optional[np.ndarray]:
        """
        Get the raw RGB image as a NumPy array.

        Returns
        -------
        Optional[np.ndarray]
            The raw RGB image data, if available.
        """
        return self.__rgb_image_raw
    
    @rgb_image_raw.setter
    def rgb_image_raw(self, rgb_image_raw: np.ndarray):
        """
        Set the raw RGB image data.

        Parameters
        ----------
        rgb_image_raw : np.ndarray
            The raw RGB image data.

        Raises
        ------
        TypeError
            If rgb_image_raw is not a NumPy array.
        """
        if not isinstance(rgb_image_raw, np.ndarray):
            raise TypeError("rgb_image_raw must be a NumPy array")
        self.__rgb_image_raw = rgb_image_raw

    @property
    def cache(self) -> Cache:
        """
        Get the cache engine instance.

        Returns
        -------
        Cache
            The Cache engine instance.
        """
        return self.__cache


    @property
    def image_files(self) -> Optional[list[str]]:
        """
        Get the list of image file paths provided to the API.

        Returns
        -------
        Optional[list[str]]
            The list of image file paths, if available.
        """
        return self.__image_files

    @property
    def number_of_images(self) -> Optional[int]:
        """
        Get the total number of images.

        Returns
        -------
        Optional[int]
            The total number of images, if available.
        """
        return self.__number_of_images
    
    @property
    def fs_model(self) -> Optional[DetectionModel]:
        """
        Returns the full-scale detection model.
        
        Returns
        -------
        Optional[DetectionModel]
            The full-scale detection model, if available.
        """
        return self.__fs_model
    
    @fs_model.setter
    def fs_model(self, model: DetectionModel):
        """
        Sets the full-scale detection model.
        
        Parameters
        ----------
        model : DetectionModel
            The full-scale detection

        Raises
        ------
        TypeError
            If model is not an instance of DetectionModel.
        """
        if not isinstance(model, DetectionModel):
            raise TypeError("fs_model must be an instance of DetectionModel")
        self.__fs_model = model

    @property
    def ss_model(self) -> Optional[DetectionModel]:
        """
        Returns the small-scale detection model.
        
        Returns
        -------
        Optional[DetectionModel]
            The small-scale detection model, if available.
        """
        return self.__ss_model
    
    @ss_model.setter
    def ss_model(self, model: DetectionModel):
        """
        Sets the small-scale detection model.
        
        Parameters
        ----------
        model : DetectionModel
            The small-scale detection model.

        Raises
        ------
        TypeError
            If model is not an instance of DetectionModel.
        """
        if not isinstance(model, DetectionModel):
            raise TypeError("ss_model must be an instance of DetectionModel")
        self.__ss_model = model

    @property
    def current_set_index(self) -> Optional[int]:
        """
        Get the current set index.

        Returns
        -------
        Optional[int]
            The current set index.
        """
        return self.__current_set_index
    
    @current_set_index.setter
    def current_set_index(self, index: int):
        """
        Set the current set index.

        Parameters
        ----------
        index : int
            The index to set as the current set index.

        Raises
        ------
        TypeError
            If the index is not an integer.
        ValueError
            If the index is out of range.
        """
        if not isinstance(index, int):
            raise TypeError("index must be an integer")
        if not (0 <= index < self.__number_of_images):
            raise ValueError("index must be within the range of image files")
        self.__current_set_index = index

    @property
    def current_test_type(self) -> Optional[TestType]:
        """
        Get the current test type.

        Returns
        -------
        Optional[TestType]
            The current test type.
        """
        return self.__current_test_type
    

# =============================================================================
# Getters && Setters && Selectors
# =============================================================================


    def reset_cache(self, number_of_images: int):
        """
        Resets the cache with a new number of images.
        
        Parameters
        ----------
        number_of_images : int
            The number of images to be stored in the cache.
        """
        self.__cache = Cache(number_of_images)

    def get_builder(self, test_type: TestType) -> BuilderApi:
        """
        Returns a BuilderApi instance for the specified test type.
        
        Parameters
        ----------
        test_type : TestType
            The type of test for the builder.
        
        Returns
        -------
        BuilderApi
            A BuilderApi instance.
        """
        if self.__last_builder_type != test_type or self.__builder is None:
            self.__builder = BuilderApi(self, test_type)
            self.__last_builder_type = test_type
        return self.__builder

    def select_image(self, index: int = -1, do_cache: bool = True) -> bool:
        """
        Selects an image by index to be the operant image and optionally caches it.
        
        Parameters
        ----------
        index : int, optional
            The index of the image to select. Defaults to the current set index.
        do_cache : bool, optional
            Whether to cache the selected image. Default is True.
        
        Returns
        -------
        bool
            True if the image was successfully selected, False otherwise.
        """
        if index == -1:
            index = self.__current_set_index

        if (
            self.__image_files is None
            or self.__number_of_images is None
            or not (0 <= index < self.__number_of_images)
            or not self.__image_files[index]
        ):
            return False

        # Load the image data from disk
        try:
            img = CoreImage.from_path(self.image_files[index])
            self.image = img
            self.rgb_image_raw = cv2.cvtColor(img.raw, cv2.COLOR_BGR2RGB)
            self.__current_set_index = index
        except Exception as e:
            # TODO: Log the error
            return False

        if do_cache:
            self.__cache.cache_image(index, self.__image)
        return True

    def get_report_output_formats(self) -> list[tuple[str, FileExtension]]:
        """
        Retrieves available report output formats.

        Returns
        -------
        list[tuple[str, FileExtension]]
            A list of available report formats.
        """
        return ReportIO.get_available_formats()
    


# =============================================================================
# IO operations
# =============================================================================


    def open_folder(self, folder_path: str, test_type : TestType) -> bool:
        """
        Opens a folder and loads image file paths into CoreApi.

        Parameters
        ----------
        folder_path : str
            Path to the folder containing image files.
        test_type : TestType
            The type of test in the image files.

        Returns
        -------
        bool
            True if images were found and loaded, False otherwise.
        """
        files = Importer.Find.image_files(folder_path)
        if files:
            self.__current_test_type = test_type
            self.__current_set_index = 0
            self.__image_files = files
            self.__number_of_images = len(files)
            self.reset_cache(len(files))
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
            self.fs_model = model
        else:
            self.ss_model = model
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
        data: list[ImageCacheStruct] = self.cache.get_all()
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
        data: list[ImageCacheStruct] = self.cache.get_all()
        formatted_data = DetectionsExportData(names=[], test_blocks=[])
        
        for img_cache in data:
            if img_cache:
                formatted_data.names.append(img_cache.img_name)
                formatted_data.test_blocks.append(img_cache.blocks)
        
        imgs: Optional[Generator[CoreImage, None, None]] = (
        CoreImage.from_paths(self.image_files, lazy=True) if save_images else None
        )
        exporter = YOLOExporter()
        return exporter.export(fullpath, formatted_data, imgs=imgs)