from core.image import CoreImage
from core.definitions.blocks import TestBlocks
from core.detection import DetectionContainer
from api.data_structs import ImageCacheStruct
from typing import List, Optional

class Cache:
    """
    A cache engine for storing image-related data in memory.

    Attributes
    ----------
    __data : List[Optional[ImageCacheStruct]]
        A list storing cached image data or None if not yet cached.
    """

    def __init__(self, number_of_images: int):
        """
        Initializes the cache with a given number of image slots.

        Parameters
        ----------
        number_of_images : int
            The number of images to be cached.
        """
        self.__data: List[Optional[ImageCacheStruct]] = [None] * number_of_images

    def cache_image(self, index: int, image: CoreImage):
        """
        Constructs the data structures for the given image and stores them in the cache at the specified index.

        Parameters
        ----------
        index : int
            The index in the cache where the image data will be stored.
        image : CoreImage
            The image to be cached.
        """
        detections = image.detections
        if not detections:
            return

        # Gather all detections, including those in cropped regions
        for crop in image.crops:
            detections.extend(crop.detections)
        container = DetectionContainer(detections)

        # Build blocks structure
        blocks: TestBlocks = image.to_block()

        # Save the structured data in cache
        self.__data[index] = ImageCacheStruct(
            image.name,
            container,
            blocks,
            questions=None,
        )

    def from_index(self, index: int) -> Optional[ImageCacheStruct]:
        """
        Retrieves the cached data at the given index.

        Parameters
        ----------
        index : int
            The index in the cache.

        Returns
        -------
        Optional[ImageCacheStruct]
            The cached image data if available, otherwise None.
        """
        return self.__data[index]

    def get_all(self) -> List[Optional[ImageCacheStruct]]:
        """
        Retrieves all cached image data.

        Returns
        -------
        List[Optional[ImageCacheStruct]]
            A list of all cached image data, where each entry may be None if not yet cached.
        """
        return self.__data
