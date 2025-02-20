from core.image import CoreImage
from core.definitions.blocks import TestBlocks
from core.detection import DetectionContainer

from api.data_structs import ImageCacheStruct



# SECTION: Cache engine

class Cache:
    """
    Cache class is used to store the data of the images in the memory.

    Attributes:
    - __data : list[ImageCacheStruct | None]
        A list with the base caching unit/object or none.
    """

    def __init__(self, number_of_images : int):
        """
        Constructor that initializes the cache with a given number of images.
        
        Attributes:
        - number_of_images : int
            The number of images to be cached.
        """
        self.__data : list[ImageCacheStruct | None] = [None] * number_of_images



    # SECTION: Cache operations 

    def cache_image(self, index : int, image : CoreImage):
        """
        Contructs the data structures for the image and saves it in the cache
        on the given index.

        Attributes:
        - index : int
            The index of the image in the cache.
        - image : CoreImage
            The image to be cached.
        """
        detections = image.detections
        if not detections:
            return
        
        # Get all the detections in the image
        crops = image.crops
        for crop in crops:
            detections.extend(crop.detections)
        container = DetectionContainer(detections)
        
        # Build blocks structure
        blocks : TestBlocks = image.to_block()
        
        # Save the data
        self.__data[index] = ImageCacheStruct(
            image.name,
            container,
            blocks,
            questions=None,
        )
    
    def from_index(self, index : int) -> ImageCacheStruct:
        return self.__data[index]

    def get_all(self) -> list[ImageCacheStruct | None]:
        return self.__data