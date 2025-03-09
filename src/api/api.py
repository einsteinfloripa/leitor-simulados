from __future__ import annotations
from typing import Generator, Optional
from pathlib import Path

import numpy as np
import cv2

from core.definitions.enums import TestType, Stage, ModelType
from core.definitions.question import TestReport
from core.definitions.blocks import TestBlocks
from core.detection import Detection
from core.image import CoreImage
from core.model import DetectionModel
from core.IO import FileExtension
from core.IO.base import Importer
from core.IO.report import ReportIO, ReportData
from core.IO.detection.export_yolo import DetectionsExportData, YOLOExporter
from core.builder import Builder

from utils.log import LoggingSystem

from .data_structs import ImageCacheStruct, ModelInfo
from .caching import Cache
from .sync_channel import ProgressTracker

logger = LoggingSystem.get_new_logger("API")

@LoggingSystem.trace_methods(logger, header="Api Call", footer="End Call")
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

        # Context Variables
        self.__image_files: Optional[list[str]] = None
        self.__number_of_images: Optional[int] = None
        self.__fs_model: Optional[DetectionModel] = None
        self.__ss_model: Optional[DetectionModel] = None
        self.__current_set_index: Optional[int] = None
        self.__current_test_type: Optional[TestType] = None
        
        # Internal only
        self.__last_builder_type : TestType = TestType.NULL
        self.__fs_model_info : ModelInfo = None
        self.__ss_model_info : ModelInfo = None


# =============================================================================
# Properties
# =============================================================================


    @property
    def image(self) -> Optional[CoreImage]:
        """
        Get the currently loaded CoreImage instance.
        This property is set by the  select_image  method.

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
        A NumPy array using RGB color pattenr as is used in the pillow lib.
        Used on computations on the image itself.
        Set by the -> select_image  method.

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

        Set on -> open_folder  and -> reset_cache  methods.

        Returns
        -------
        Cache
            The Cache engine instance.
        """
        return self.__cache


    @property
    def image_files(self) -> Optional[list[str]]:
        """
        Get the list of image file paths found on the provided folder.
        
        Set by the -> open_folder  method.

        Returns
        -------
        Optional[list[str]]
            The list of image file paths, if available.
        """
        return self.__image_files

    @property
    def number_of_images(self) -> Optional[int]:
        """
        Get the total number of image paths.
        
        Set by the -> open_folder  method.

        Returns
        -------
        Optional[int]
            The total number of images, if available.
        """
        return self.__number_of_images
    
    @property
    def fs_model(self) -> Optional[DetectionModel]:
        """
        Returns the detection model selected for the first stage detection.
        
        Set by the -> select_model  method.

        Returns
        -------
        Optional[DetectionModel]
            The full-scale detection model, if available.
        """
        return self.__fs_model

    @property
    def ss_model(self) -> Optional[DetectionModel]:
        """
        Returns the detection model selected for the second stage detection.
        
        Set by the -> select_model  method.

        Returns
        -------
        Optional[DetectionModel]
            The small-scale detection model, if available.
        """
        return self.__ss_model

    @property
    def current_set_index(self) -> Optional[int]:
        """
        Get the current set index. The index is position of the image path
        on the list of image files -> image_files.
        
        Set by the -> select_image  method.

        Returns
        -------
        Optional[int]
            The current set index.
        """
        return self.__current_set_index

    @property
    def current_test_type(self) -> Optional[TestType]:
        """
        Get the current test type.
        
        Set on the -> open_folder  method.
        
        *Is User provided on the arguments of the method.

        Returns
        -------
        Optional[TestType]
            The current test type.
        """
        return self.__current_test_type
    

# =============================================================================
# Getters && Setters && Selectors
# =============================================================================

    def get_available_models(self) -> list[ModelInfo]:
        """
        Retrieves the available model names.

        Returns
        -------
        list[ModelInfo]
            A list of available model names.
        """
        file_paths = Importer.Find.model_files()
        return [ModelInfo.from_models_path(path) for path in file_paths]

    def reset_cache(self, number_of_images: int):
        """
        Resets the cache with a new number of images.
        
        Parameters
        ----------
        number_of_images : int
            The number of images to be stored in the cache.
        """
        self.__cache = Cache(number_of_images)


    def select_image(self, index: int = -1, reload=False) -> bool:
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
        elif index == self.__current_set_index and not reload:
            return True

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
            logger.exception(f"Failed to load image at index {index}: {e}")
            return False

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
    
    def select_model(self, model_info: ModelInfo, stage: Stage = Stage.NULL) -> bool:
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

        Raises
        ------
        ValueError
            If the model does not support the selected stage.
        """
        
        # Check if the model is already loaded
        if stage == Stage.FIRST and self.__fs_model_info == model_info:
            return True
        elif stage == Stage.SECOND and self.__ss_model_info == model_info:
            return True

        # Check if the model supports the selected stage
        target_stage = model_info.target_stage    
        if target_stage is not Stage.BOTH and target_stage != stage:
            raise ValueError(
                f"Model {model_info.name} does not support stage {stage.name}"
            )
        
        # Load the model
        model_path = model_info.rel_path
        if model_info.model_type == ModelType.EFSCANALGO:
            model = DetectionModel.from_models_path(model_path, stage, self.current_test_type)
        else:
            model = DetectionModel.from_models_path(model_path, stage)
        
        if not model:
            return False
        if stage == Stage.SECOND:
            self.__ss_model = model
            self.__ss_model_info = model_info
            logger.info(f'"{model_info.name}" loaded for stage {stage.name}')
        else:
            self.__fs_model = model
            self.__fs_model_info = model_info
            logger.info(f'"{model_info.name}" loaded for stage {stage.name}')
        return True

    def get_report(self, index: int = -1) -> Optional[TestReport]:
        """
        Get the report for the selected image.

        Parameters
        ----------
        index : int, optional
            The index of the image to process. Defaults to the current set index.

        Returns
        -------
        Optional[TestReport]
            The report for the selected image, if available.
        """
        if index == -1:
            index = self.current_set_index
        img_cache: Optional[ImageCacheStruct] = self.cache.from_index(index)
        if img_cache is None:
            return None
        return img_cache.report 

    def has_report(self, index: int = -1) -> bool:
        """
        Check if a report is available for the selected image.

        Parameters
        ----------
        index : int, optional
            The index of the image to process. Defaults to the current set index.

        Returns
        -------
        bool
            True if a report is available, False otherwise.
        """
        if index == -1:
            index = self.current_set_index
        return (
            self.cache.from_index(index) is not None \
            and self.cache.from_index(index).report is not None
        )

# =============================================================================
# Building answers report operations
# =============================================================================


    def build_report(self, index : int = -1):
        """
        Builds a report for the selected image. ( i.e. try to get the 
        answers for the questions in the image based on the detections )

        Parameters
        ----------
        index : int, optional
            The index of the image to process. Defaults to the current set index.

        Raises
        ------
        ValueError
            If no cache data is found for the selected image.
        """
        # Get the index of the image to process
        if index == -1:
            index = self.current_set_index

        # Retrieve cached data
        img_cache: Optional[ImageCacheStruct] = self.cache.from_index(index)
        if img_cache is None:
            raise ValueError("No cache data found for the current image")
        
        blocks: TestBlocks = img_cache.blocks
        
        # Get the builder engine
        builder = Builder.from_test_type(self.current_test_type)

        # Initialize the report data structure
        report = TestReport.from_test_type(self.current_test_type)

        # Resolve the CPF owner
        report.set_owner_cpf(builder.resolve_cpf(blocks.cpf_block))

        # Process each question block
        for block in blocks.questions_blocks:
            report.update_answers(builder.resolve_question_block(block))

        # Update cache with resolved questions
        img_cache.report = report



# =============================================================================
# Detection operations
# =============================================================================


    def run_detection_pipeline(
            self,
            fs_score_threshold: float,
            ss_score_threshold: float
            ):
        """
        Runs the detection pipeline for the currently selected image.

        Parameters
        ----------
        fs_score_threshold : float
            The score threshold for the full-scale detection model.
        ss_score_threshold : float
            The score threshold for the small-scale detection model.

        Raises
        ------
        ValueError
            If the models are not correctly loaded.
        """
        # Check if enought models are loaded
        if not self.__fs_model \
           or ( 
                not self.__ss_model 
                and not self.__fs_model.target_stage == Stage.BOTH
            ):
            raise ValueError("Bad models setup")
                
        # Run the detection pipeline
        Detection.set_label_map(self.fs_model.label_map)
        self.image.make_detections_with_model(
            self.__fs_model, fs_score_threshold
        )
        self.image.make_cropped()
        Detection.set_label_map(self.ss_model.label_map)
        for crop in self.image.crops:
            crop.make_detections_with_model(
                self.__ss_model, ss_score_threshold
            )

        # Cache the detections
        self.cache.cache_image(self.current_set_index, self.image)

    def run_detection_pipeline_for_all(
            self,
            fs_score_threshold: float,
            ss_score_threshold: float,
            progress_queue: Optional[ProgressTracker] = None
        ):
        """
        Runs the detection pipeline for all images in the current set.

        Parameters
        ----------
        fs_params : DetectionParameters
            Parameters for the full-scale detection model.
        ss_params : DetectionParameters
            Parameters for the small-scale detection model.
        progress_queue : Optional[ProgressTracker], optional
            A progress tracker to monitor the pipeline, by default None.

        Raises
        ------
        ValueError
            If the models are not correctly

        Returns
        -------
        bool
            True if the pipeline was successfully run, False otherwise.
        """

        # Check if models are loaded
        if not self.__fs_model \
           or ( 
                not self.__ss_model 
                and not self.__fs_model.target_stage == Stage.BOTH
            ):
            raise ValueError("Cannot run detection pipeline without valid models")
        
        # Set up the progress tracker
        if progress_queue:
            if not progress_queue.is_zero():
                raise ValueError("Progress tracker must be reset before use")
            progress_queue.set_total_steps(self.number_of_images)

        # Run the detection pipeline for all images
        for i in range(self.number_of_images):
            # Select the image
            self.select_image(i)
            # Run the detection pipeline
            Detection.set_label_map(self.fs_model.label_map)
            self.image.make_detections_with_model(
                self.__fs_model, fs_score_threshold
            )
            self.image.make_cropped()
            Detection.set_label_map(self.ss_model.label_map)
            for crop in self.image.crops:
                crop.make_detections_with_model(
                    self.__ss_model, ss_score_threshold
            )

            # Cache the detections
            self.cache.cache_image(self.current_set_index, self.image)

            # Update the progress tracker
            if progress_queue:
                progress_queue.increment()
            
            # Check if the progress tracker is still running
            if not progress_queue.running():
                break
        self.select_image(0)
        return True


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
            self.__image_files = files
            self.__number_of_images = len(files)
            self.reset_cache(len(files))
            return True
        return False

    

    def save_report(self, fullpath: Path, exporter_name: str = "DefaultJSON"):
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
        formatted_data = ReportData(test_type=self.current_test_type)
        
        for img_cache in data:
            if img_cache:
                formatted_data.names.append(img_cache.img_name)
                formatted_data.test_reports.append(img_cache.report)
        
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