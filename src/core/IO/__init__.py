from abc import ABC, abstractmethod
import inspect
from functools import wraps
from pathlib import Path
from enum import Enum

# SECTION: Variable definitions

# Images
ACCEPTED_IMAGE_EXTENTIONS = {'.png', '.jpg', '.jpeg'}
ACCEPTED_MODELS_EXTENTIONS = {'.tflite', '.py', '.pb'}
# Models
MODELS_PATH = Path(__file__).parent.parent.parent / 'models'



# SECTION: Enum classes definitions

class FileExtension(Enum):
    """
    This enum class contains the supported formats for the
    export and import of detections.
    """
    CSV = '.csv'
    JSON = '.json'
    EXCEL = '.xlsx'
    TXT = '.txt'
    


# SECTION: Base classes definitions

class Importer():

    class Find:
        """
        This class contains static methods to find files in a given
        folder.
        """
        @staticmethod
        def image_files(folder_path : str, recursive : bool = False):
            folder = Path(folder_path)
            if recursive:
                files = [
                        str(f) for f in folder.rglob('*.*') \
                        if f.suffix.lower() in ACCEPTED_IMAGE_EXTENTIONS
                ]
            else:
                files = [
                        str(f) for f in folder.glob('*.*') \
                        if f.suffix.lower() in ACCEPTED_IMAGE_EXTENTIONS
                ]
            return files
        
        @staticmethod
        def model_files(folder_path : str, recursive : bool = False):
            folder = Path(folder_path)
            if recursive:
                files = [
                        str(f) for f in folder.rglob('*.*') \
                        if f.suffix.lower() in ACCEPTED_MODELS_EXTENTIONS
                ]
            else:
                files = [
                        str(f) for f in folder.glob('*.*') \
                        if f.suffix.lower() in ACCEPTED_MODELS_EXTENTIONS
                ]
            return files


class Exporter(ABC):

    @property
    @abstractmethod
    def extension(self):
        self.extension

    @staticmethod
    def folder_export(func : callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get the path parameters parameters
            fullpath = kwargs.get('out_fullpath', None)
            # Convert to Path object if it is a string
            if isinstance(fullpath, str):
                fullpath = Path(fullpath)
            # Make the directory
            # If the directory already exists, raise an error
            fullpath.parent.mkdir()
            # Call the actual function
            status = func(self, *args, **kwargs)
            if not status:
                fullpath.rmdir()
            return status

        return wrapper

