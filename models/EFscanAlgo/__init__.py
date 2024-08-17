from __future__ import annotations
import importlib

from core.image import Image
from EFscanAlgo.ef_defs import SimufscData, SimuenemData, SimulinhoData, PSData

class Scanner:
    
    def get_test_data(self, key):
        return self.__test_data.__dict__.get(key)
    
    def __init__(self, config : dict):
        # Import and set the correct pipline
        import_string = f"EFscanAlgo.{config['model']['stage'].lower()}.{config['model']['name']}".strip('.py')
        try:
            pipeline_module = importlib.import_module(import_string)
            self.__detect_func = getattr(pipeline_module, "detect")
            init_pipeline_func = getattr(pipeline_module, "init_pipeline", None)
            
        except ImportError:
            raise ImportError(f"Could not import {import_string}")

        # Get the relevant data
        test_type = config["test"]
        if test_type.upper() == "SIMUFSC":
            self.__test_data = SimufscData
        elif test_type.upper() == "SIMUENEM":
            self.__test_data = SimuenemData
        elif test_type.upper() == "SIMULINHO":
            self.__test_data = SimulinhoData
        elif test_type.upper() == "PS":
            self.__test_data = PSData
        else:
            raise ValueError("Invalid test type")
        
        # Calls init_pipeline if one exists
        if init_pipeline_func is not None:
            try:
                init_pipeline_func(self, config)
            except Exception as e:
                raise ValueError(f"Error while initializing pipeline: {e}")
            

    def detect(self, image : Image):
        return self.__detect_func(self, image)

