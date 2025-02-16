import os
import shutil
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
ROOT_PATH = Path(__file__).parent.parent.parent
MODELS_PATH = ROOT_PATH / 'models'


# SECTION: Enum classes definitions

class FileExtension(Enum):
    """
    This enum class contains the supported formats for the
    export and import of detections.
    """
    FOLDER = ''
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
            # Get an argument or kwarg named 'fullpath'
            fullpath = None
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            for name, value in bound_args.arguments.items():
                if name == 'fullpath':
                    fullpath = value
            # Convert to Path object if it is a string
            if isinstance(fullpath, str):
                fullpath = Path(fullpath)
            # Make the directory
            # If the directory already exists, raise an error
            fullpath.mkdir()
            # Call the actual function
            try:
                status = func(self, *args, **kwargs)
                if not status:
                    return False
            except Exception as e:
                Exporter.clear_folder(fullpath)
                fullpath.rmdir()
                return False
            return True

        return wrapper

    @staticmethod
    def clear_folder(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):  
                os.remove(item_path)  # Remove files and symlinks
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove subdirectories and their contents