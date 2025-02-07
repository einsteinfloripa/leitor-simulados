from .base import Detection

class DetectionContainer:
    
    def __init__(self, detections=[]) -> None:
        self.__detections : list[Detection] = detections
        self.__by_type : dict[Detection.Type, list[Detection]] = None
        self.__build_by_type()


    def add_detection(self, detection : Detection) -> None:
        self.__detections.append(detection)
        if detection.class_type not in self.__by_type:
            self.__by_type[detection.class_type] = []
        self.__by_type[detection.class_type].append(detection)

    def set_detections(self, detections : list[Detection]) -> None:
        self.__detections = detections
        self.__build_by_type()

    def get_detections(self) -> list[Detection]:
        return self.__detections

    def get_by_type(
            self,
            class_types : list[Detection.Type],
            to_list : bool = False
        ) -> dict[Detection.Type, list[Detection]]:
        if isinstance(class_types, Detection.Type):
            class_types = [class_types]
        if to_list:
            return [
                item for class_type in class_types
                if class_type in self.__by_type
                for item in self.__by_type[class_type]
            ]
        return {k: v for k, v in self.__by_type.items() if k in class_types}

    def empty(self) -> bool:
        return len(self.__detections) == 0

    # Construction
    def __build_by_type(self) -> None:
        self.__by_type = {}
        for detection in self.__detections:
            if detection.class_type not in self.__by_type:
                self.__by_type[detection.class_type] = []
            self.__by_type[detection.class_type].append(detection)
