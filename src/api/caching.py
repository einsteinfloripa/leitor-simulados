from core.image import Image
from core.builder.data_structs import TestBlocks
from api.data_structs import ImageCacheStruct


class Cache:

    def __init__(self, number_of_images : int):
        self.data : list[ImageCacheStruct] = [None] * number_of_images

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
        
        crops = image.crops
        for crop in crops:
            detections.extend(crop.detections)
        # Build the data structures
        blocks : TestBlocks = image.to_blocks()
        coord_to_det_map = {}
        coord_by_type = {}
        coords = []
        for detection in detections:
            coord = detection.to_coords()
            coord_to_det_map[coord] = detection
            coords.append(coord)
            try:
                coord_by_type[detection.class_type].append(coord)
            except KeyError:
                coord_by_type[detection.class_type] = [coord]
        # Save the data
        self.data[index] = ImageCacheStruct(
            detections,
            crops,
            blocks,
            coords,
            coord_to_det_map,
            coord_by_type
            )
    
    def from_index(self, index : int) -> ImageCacheStruct:
        return self.data[index]
