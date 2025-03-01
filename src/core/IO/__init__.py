from pathlib import Path
from enum import Enum

# CoreImages
ACCEPTED_IMAGE_EXTENTIONS = {'.png', '.jpg', '.jpeg'}
ACCEPTED_MODELS_EXTENTIONS = {'.tflite', '.py', '.pt'}
# Paths
ROOT_PATH = Path(__file__).parent.parent.parent.parent # Tataravo raiz
MODELS_PATH = ROOT_PATH / 'models'
EXEMPLES_PATH = ROOT_PATH / 'exemple_images'


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
    