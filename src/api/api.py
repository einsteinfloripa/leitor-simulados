import numpy as np
import cv2

from core.image import Image
from core.model import load_model, DetectionModel
from definitions import Stage, TestType

from utils.filehandler import FileHandler

from api.caching import Cache
from api.builder import Builder

class CoreApi():
    def __init__(self):
        # Image
        self.__image_files : list[str] = None
        self.__image : Image = None
        self.__rgb_image_raw : np.ndarray = None
        self.__number_of_images : int = None
        self.__cache : Cache = Cache(0)
        self.__builder : Builder = None
        self.__last_builder_type : TestType = TestType.NULL
        # Models
        self.__fs_model : DetectionModel = None
        self.__ss_model : DetectionModel = None

    ## Getters && Setters ##
    # Image
    def get_image(self) -> Image:
        return self.__image
    def set_image(self, image : Image):
        self.__image = image
    # Image Files
    def get_image_files(self) -> list[str]:
        return self.__image_files
    def set_image_files(self, image_files : list[str]):
        self.__image_files = image_files
    # Number of Images
    def get_number_of_images(self) -> int:
        return self.__number_of_images
    def set_number_of_images(self, number_of_images : int):
        self.__number_of_images = number_of_images
    def get_rbg_image_raw(self) -> np.ndarray:
        return self.__rgb_image_raw
    def set_rbg_image_raw(self, rbg_image_raw : np.ndarray):
        self.__rgb_image_raw = rbg_image_raw

    # Cache
    def get_cache(self) -> Cache:
        return self.__cache
    # Builder
    def get_builder(self, test_type : TestType) -> Builder:
        if self.__last_builder_type != test_type:
            self.__builder = Builder.from_test_type(test_type)
        return self.__builder
    
    # Models
    # fs_model
    def get_fs_model(self) -> DetectionModel:
        return self.__fs_model
    def set_fs_model(self, fs_model : DetectionModel):
        self.__fs_model = fs_model
    # ss_model
    def get_ss_model(self) -> DetectionModel:
        return self.__ss_model
    def set_ss_model(self, ss_model : DetectionModel):
        self.__ss_model = ss_model
    

    ## Operation Functions ##
    def load_image(self, index : int, do_cache = True) -> bool:
        if index < 0 or index >= self.__number_of_images or not self.__image_files[index]:
            return False
        # Load the image at the given index
        self.__image = Image.from_path(self.__image_files[index])
        self.__rgb_image_raw = cv2.cvtColor(self.__image.raw, cv2.COLOR_BGR2RGB)
        # Cache the image if needed
        if do_cache:
            self.__cache.cache_image(index, self.__image)
        return True

    def open_folder(self, folder_path : str) -> bool:
        files = FileHandler.find_image_files(folder_path)
        if files:
            # Save the image paths
            self.__image_files = files
            # Set the cache list
            self.__number_of_images = len(files)
            self.__cache = Cache(self.__number_of_images)
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
            self.__fs_model = model
        else:
            self.__ss_model = model
        return True
