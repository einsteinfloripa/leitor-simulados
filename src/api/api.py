import numpy as np
import cv2

from core.image import Image
from core.models import load_model, DetectionModel
from core.defs import Stage

from utils.filehandler import FileHandler

from api.caching import Cache


class CoreApi():
    def __init__(self):
        # Image
        self._image_files : list[str] = None
        self._image : Image = None
        self._rgb_image_raw : np.ndarray = None
        self._number_of_images : int = None
        self._cache : Cache = Cache(0)
        # Models
        self._fs_model : DetectionModel = None
        self._ss_model : DetectionModel = None

    ## Getters && Setters ##
    def get_image(self) -> Image:
        return self._image
    
    def get_cache(self) -> Cache:
        return self._cache
    
    def get_rbg_image_raw(self) -> np.ndarray:
        return self._rbg_image_raw


    ## Operation Functions ##
    def load_image(self, index : int, do_cache = True) -> bool:
        if index < 0 or index >= self._number_of_images or not self._image_files[index]:
            return False
        # Load the image at the given index
        self._image = Image.from_path(self._image_files[index])
        self._rbg_image_raw = cv2.cvtColor(self._image.raw, cv2.COLOR_BGR2RGB)
        # Cache the image if needed
        if do_cache:
            self._cache.cache_image(index, self._image)
        return True

    def open_folder(self, folder_path : str) -> bool:
        files = FileHandler.find_image_files(folder_path)
        if files:
            # Save the image paths
            self._image_files = files
            # Set the cache list
            self._number_of_images = len(files)
            self._cache = Cache(self._number_of_images)
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
            self._fs_model = model
        else:
            self._ss_model = model
        return True
