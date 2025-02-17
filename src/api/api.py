import numpy as np


from core.image import CoreImage
from core.model import DetectionModel
from core.definitions import TestType

from .caching import Cache
from .builder import BuilderApi
from .IO import IOApi



# SECTION: CoreApi class

class CoreApi():

    ## Initialization ##
    def __init__(self):
        # CoreImage
        self.__image_files : list[str] = None
        self.__image : CoreImage = None
        self.__rgb_image_raw : np.ndarray = None
        self.__number_of_images : int = None
        self.__cache : Cache = Cache(0)
        self.__io : IOApi = IOApi(self)
        self.__builder : BuilderApi = None
        self.__last_builder_type : TestType = TestType.NULL
        # Models
        self.__fs_model : DetectionModel = None
        self.__ss_model : DetectionModel = None

    # IO    
    @property
    def io(self):
        return self.__io

    # Cache
    @property
    def cache(self):
        return self.__cache
    
    def set_cache(self, number_of_images : int):
        self.__cache = Cache(number_of_images)


    ## Getters && Setters ##

    # Image
    
    def get_image(self) -> CoreImage:
        return self.__image
    def set_image(self, image : CoreImage):
        self.__image = image
    
    # CoreImage Files
    def get_image_files(self) -> list[str]:
        return self.__image_files
    def set_image_files(self, image_files : list[str]):
        self.__image_files = image_files
    
    # Number of CoreImages
    def get_number_of_images(self) -> int:
        return self.__number_of_images
    def set_number_of_images(self, number_of_images : int):
        self.__number_of_images = number_of_images
    
    # RGB CoreImage Raw
    def get_rbg_image_raw(self) -> np.ndarray:
        return self.__rgb_image_raw
    def set_rbg_image_raw(self, rbg_image_raw : np.ndarray):
        self.__rgb_image_raw = rbg_image_raw

    # Builder
    def get_builder(self, test_type : TestType) -> BuilderApi:
        if self.__last_builder_type != test_type:
            self.__builder = BuilderApi(self, test_type)
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
        if self.__io.load_image(index):
            # Cache the image if needed
            if do_cache:
                self.__cache.cache_image(index, self.__image)
            return True
        return False