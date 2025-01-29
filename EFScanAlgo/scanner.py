from dataclasses import dataclass
import importlib

from src.core.image import Image
from utils.log import get_new_logger
from ef_defs import (
    SimuenemData, 
    SimufscData, 
    SimulinhoData, 
    PSData
)

@dataclass
class Config:
    model_name : str
    test : str
    stage : str


class Scanner:
    
    def get_test_data(self, key):
        return self.__test_data.__dict__.get(key)
    
    def __init__(self, config : Config):
        # Set configs
        self.config = config
        # Set the logger
        self.logger = get_new_logger(f"EFscanAlgo({config.stage})")
        # Import and set the correct pipline
        import_string = f"EFscanAlgo.{config.stage.lower()}.{config.model_name}".strip('.py')
        try:
            pipeline_module = importlib.import_module(import_string)
        except ImportError:
            raise ImportError(f"Could not import {import_string}")
        try:
            self.__detect_func = getattr(pipeline_module, "detect")
            init_pipeline_func = getattr(pipeline_module, "init_pipeline", None)
        except AttributeError:
            raise AttributeError(f"Could not find detect function in {import_string}")   

        # Get the relevant data
        test_type = config["test"]
        if test_type.upper() == "SIMUFSC":
            self.__test_data = SimufscData
        elif test_type.upper() == "SIMUENEM":
            raise NotImplementedError("SIMUENEM data not implemented yet")
            self.__test_data = SimuenemData
        elif test_type.upper() == "SIMULINHO":
            raise NotImplementedError("SIMULINHO data not implemented yet")
            self.__test_data = SimulinhoData
        elif test_type.upper() == "PS":
            raise NotImplementedError("PS data not implemented yet")
            self.__test_data = PSData
        else:
            raise ValueError("Invalid test type")
        
        # Calls init_pipeline if one exists
        if init_pipeline_func is not None:
            try:
                init_pipeline_func(self, config)
            except Exception as e:
                raise ValueError(f"Error while initializing pipeline: {e}")
        self.logger.info(f"Scanner initialized with pipeline: {config.model_name}")
            

    def detect(self, image : Image):
        self.logger.info(f"Detecting on image {image.name}")

        try:
            detections = self.__detect_func(self, image)
        except Exception as e:
            self.logger.error(f"[FALIED] {image.name} - {e}")
            raise e
        
        self.logger.info(f"[Done!]")
        return detections
