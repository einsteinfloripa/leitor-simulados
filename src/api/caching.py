from core.image import Image
from core.builder.data_structs import TestBlocks
from api.data_structs import ImageCacheStruct
from core.detection import DetectionContainer

class Cache:

    def __init__(self, number_of_images : int):
        self.data : list[ImageCacheStruct | None] = [None] * number_of_images

    def cache_image(self, index : int, image : Image):
        """
        Contructs the data structures for the image and saves it in the cache
        on the given index.

        Attributes:
        - index: The index of the image in the cache.
        - image: The image to be cached.
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
        self.data[index] = ImageCacheStruct(
            container,
            crops,
            blocks,
        )
    
    def from_index(self, index : int) -> ImageCacheStruct:
        return self.data[index]
