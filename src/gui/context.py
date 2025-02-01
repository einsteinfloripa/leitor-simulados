from core.image import Image as CoreImage
from core.image import ImageCache
from core.defs import Stage
from core.models import load_model
from core.detection import Detection, DetectionCoords

from utils.filehandler import FileHandler

class Callback:
    
    def __init__(self):
        self.callback_list = []

    def add_callback(self, callback : callable):
        if not callable(callback):
            raise ValueError("Callback must be a callable function")
        self.callback_list.append(callback)
    
    def __call__(self):
        for callback in self.callback_list:
            callback()

class AppContextData:
    """
    Class for storing the current state of the application and its variables
    """
    # IMAGE
    # Image paths
    image_files = []
    # Current image
    image : CoreImage = None
    image_cache : list[ImageCache] = None
    number_of_images = -1

    # MODELS
    # Models
    fs_model = None
    fs_score_threshold = 0.5
    ss_model = None
    ss_score_threshold = 0.5

    # Group Callbacks
    folder_loaded_callback : Callback = Callback()
    

    ## Operation Functions ##
    @classmethod
    def load_image_to_context(cls, index : int, do_cache = True) -> None:
        # Load the image at the given index
        cls.image = CoreImage.from_path(cls.image_files[index])
        # Cache the image if needed
        if do_cache:
            cls.image_index = index
            cls.image_cache[index] = cls.image.to_cache()

    @classmethod    
    def open_folder(cls, folder_path : str) -> None:
        files = FileHandler.find_image_files(folder_path)
        if files:
            # Save the image paths
            cls.image_files = files
            # Set the cache list
            cls.number_of_images = len(files)
            cls.image_cache = [None] * cls.number_of_images
            # Load the first image
            cls.load_image_to_context(0, do_cache=False)

    @classmethod
    def load_model_to_context(
            cls,
            model_path : str,
            stage : Stage = Stage.NULL
            ) -> None:
        try:
            model = load_model(model_path, stage)
            if stage == Stage.FIRST:
                cls.fs_model = model
            else:
                cls.ss_model = model
            return True
        except Exception as e:
            print(e)
            return False
