from __future__ import annotations

import os
import shutil
import inspect
import json
import numpy as np
import cv2
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
        
    @staticmethod
    def load_cv2_image(image_path : str) -> np.ndarray:
        return cv2.imread(image_path)


class Exporter(ABC):

    _logger = LoggingSystem.get_new_logger(__name__)

    @property
    @abstractmethod
    def extension(self):
        self.extension

    @classmethod    
    def folder_export(cls, func : callable):
        """
        Decorator to automatically create a folder for the export
        function. If the operation fails (i.e. the decorated function returns false
        or raises an error), the folder is deleted.

        The decorator expects the decorated function to have a
        paeameter named 'out_dir' which is the path of the folder
        the decorated function is meant to write on.

        Usage example:

        @Exporter.folder_export
        def export(self, out_dir : Path, data : dict) -> bool:
            ...
            return True
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # Get an argument or kwarg named 'out_dir'
            out_dir = None
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            out_dir = bound_args.arguments.get('out_dir')

            if out_dir is None:
                cls._logger.error("The decorated function must have an argument named 'out_dir'")
                return False
            else:
                cls._logger.debug(f"out_dir parameter found: {out_dir}")

            try:
                if not isinstance(out_dir, Path):
                    out_dir = Path(out_dir)
                    # Also update the arg
                    bound_args.arguments['out_dir'] = out_dir
                # Make the directory
                # If the directory already exists, raise an error
                out_dir.mkdir()
                
            
                # Call the actual function
                status = func(*bound_args.args, **bound_args.kwargs)
                cls._logger.debug(f"Function status returned: {status}")
            except Exception as e:
                if e is IOError or e is FileExistsError:
                    Exporter._logger.error(e)
                    Exporter.clear_folder(out_dir)
                    return False
                else:
                    Exporter._logger.exception(e)
                    Exporter.clear_folder(out_dir)
                    raise e
            return status

        return wrapper

    @staticmethod
    def clear_folder(folder_path : str | Path):
        Exporter._logger.debug(f"Deleting folder {folder_path}")
        # Transform the path to a Path object if it is a string
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        # Check if the folder exists
        if not folder_path.exists():
            return
        # Recursively delete the folder and its contents
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

    @staticmethod
    def save_cv2_image(out_fullpath : str, image : np.ndarray):
        cv2.imwrite(out_fullpath, image)
            
            