from __future__ import annotations

import os
import shutil
import inspect
import json
from pathlib import Path
from typing import Generator
from functools import wraps
from abc import ABC, abstractmethod

from core.detection.label_map import LabelMap
from core.definitions.blocks import TestBlocks
from core.image import CoreImage

from utils.log import LoggingSystem

from . import (
    IOError,
    ACCEPTED_IMAGE_EXTENTIONS,
    ACCEPTED_MODELS_EXTENTIONS,
    MODELS_PATH
)


class Importer():

    _logger = LoggingSystem.get_new_logger(__name__)

    class JSON:
        @staticmethod
        def load_label_maps(serch_dir : Path = MODELS_PATH):
            file = serch_dir / 'LabelMaps.json'
            if not file.exists():
                return None
            with open(file, 'r') as f:
                label_maps : dict = json.load(f)
                return label_maps
            return None

    class Find:
        """
        This class contains static methods to find files in a given
        folder.
        """
        @staticmethod
        def image_files(folder_path : str, recursive : bool = False):
            Importer._logger.info(f"Searching for images in {folder_path}")
            
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
            
            Importer._logger.debug(f"Found {len(files)} images: {files}")
            return files
        
        @staticmethod
        def model_files(
            folder_path : str = MODELS_PATH, 
            recursive : bool = True
        ) -> list[str]:
            Importer._logger.info(f"Searching for models in {folder_path}")

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

            Importer._logger.debug(f"Found {len(files)} models: {files}")
            return files

class Exporter(ABC):

    _logger = LoggingSystem.get_new_logger(__name__)

    @property
    @abstractmethod
    def extension(self):
        self.extension

    
    def folder_export(func : callable):
        """
        Decorator to create a folder for the output before calling the 
        decorated function.
        If the function fails, the folder is deleted.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):

            # Get an argument or kwarg named 'fullpath'
            fullpath = None
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            fullpath = bound_args.arguments.get('fullpath')
            
            # Make the directory
            # If the directory already exists, raise an error
            fullpath.mkdir()
            
            # Call the actual function
            try:
                status = func(*args, **kwargs)
                if not status:
                    Exporter.clear_folder(fullpath)
                    return False
            except Exception as e:
                if isinstance(e, IOError):
                    Exporter._logger.error(e)
                else:
                    Exporter._logger.exception(e)
                Exporter.clear_folder(fullpath)
                return False
            return True

        return wrapper

    @staticmethod
    def clear_folder(folder_path : str | Path):
        Exporter._logger.debug(f"Deleting folder {folder_path}")
        
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):  
                os.remove(item_path)  # Remove files and symlinks
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove subdirectories and their contents
        folder_path.rmdir()  # Remove the directory itself
    
    
    @staticmethod
    def save_images(
            destination : list[str],
            images : Generator[CoreImage, None, None],
            blockss : list[TestBlocks]
        ):
        for dest, img, blocks in zip(destination, images, blockss):
            Exporter.save_image(dest, img, blocks)

    @staticmethod
    def save_image(
            dest : str,
            image : CoreImage,
            blocks : TestBlocks
        ):
        if not os.path.exists(dest):
            os.makedirs(dest)
        image.import_blocks(blocks)
        image.save(dest)
        for crop in image.crops:
            crop.save(dest)

            
            