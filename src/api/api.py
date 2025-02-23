from typing import Optional
import numpy as np

from core.image import CoreImage
from core.model import DetectionModel
from core.definitions import TestType

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
        self.__io: IOApi = IOApi(self)
        self.__builder: Optional[BuilderApi] = None

        # Context Variables
        self.__image_files: Optional[list[str]] = None
        self.__number_of_images: Optional[int] = None
        self.__fs_model: Optional[DetectionModel] = None
        self.__ss_model: Optional[DetectionModel] = None
        self.__current_set_index: Optional[int] = None
        
        # Internal only
        self.__last_builder_type: TestType = TestType.NULL

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
    def io(self) -> IOApi:
        """
        Get the IO API instance.

        Returns
        -------
        IOApi
            The IO API instance.
        """
        return self.__io

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

    @image_files.setter
    def image_files(self, image_files: list[str]):
        """
        Set the list of image file paths.

        Parameters
        ----------
        image_files : list[str]
            The list of image file paths.

        Raises
        ------
        TypeError
            If image_files is not a list of strings.
        """
        if not isinstance(image_files, list) or not all(isinstance(item, str) for item in image_files):
            raise TypeError("image_files must be a list of strings")
        self.__image_files = image_files

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
    
    @number_of_images.setter
    def number_of_images(self, number_of_images: int):
        """
        Set the total number of images.

        Parameters
        ----------
        number_of_images : int
            The total number of images.

        Raises
        ------
        TypeError
            If number_of_images is not an integer.
        """
        if not isinstance(number_of_images, int):
            raise TypeError("number_of_images must be an integer")
        self.__number_of_images = number_of_images

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


    ## Methods ##

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

        if self.__io.load_image(index):
            if do_cache:
                self.__cache.cache_image(index, self.__image)
            return True
        return False
