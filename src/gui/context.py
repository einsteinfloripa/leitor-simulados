from core.image import Image as CoreImage
from core.image import ImageCache

from core.models import load_model
from utils.misc import parse_model
from core.detection import Detection, DetectionCoords

from utils.filehandler import FileHandler

class AppContextData:

    #Enum Defs
    class ModelStage:
        FIRST_STAGE = "FIRST_STAGE"
        SECOND_STAGE = "SECOND_STAGE"

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
    folder_loaded_callback = []
    

    ## Operation Functions ##
    @classmethod
    def load_image_to_context(cls, index : int) -> None:
        # Load the image at the given index
        cls.image = CoreImage.from_path(cls.image_files[index])
        # Set all the other variables
        cls.image_index = index
        cls.image_cache = cls.image.to_cache()

    @classmethod    
    def open_folder(cls, folder_path : str) -> None:
        files = FileHandler.get_img_files(folder_path)
        if files:
            # Save the image paths
            cls.image_files = files
            # Set the cache list
            n_imgs = len(files)
            
            cls.image_cache = [None] * n_imgs
            # Load the first image
            cls.load_image_to_context(0)

    @classmethod
    def load_model_to_context(
            cls,
            model_path : str,
            stage = ModelStage.FIRST_STAGE
            ) -> None:
        # Parse the model path
        init_dict = parse_model(model_path)
        # Try to load the model
        if init_dict:
            model = load_model(model_path)
            if stage == AppContextData.ModelStage.FIRST_STAGE:
                cls.fs_model = model
            else:
                cls.ss_model = model
