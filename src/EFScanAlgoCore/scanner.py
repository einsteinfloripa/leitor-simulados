import importlib

from core.image import CoreImage
from core.definitions import Stage
from core.definitions.test_defs import TestType

from .ef_defs import (
    SimuenemData, 
    SimufscData,
    SimulinhoData, 
    PSData
)



# SECTION: Config information

from dataclasses import dataclass
@dataclass
class Config:
    model_name : str
    test_type : TestType
    stage : Stage



# SECTION: Scanner base class

class Scanner:


    ## Initialization ##

    def __init__(
            self,
            model_name : str,
            test_type : TestType,
            stage : Stage
        ):
        
        # Set configs
        self.config = Config(
            model_name = model_name,
            test_type = test_type,
            stage = stage
        )
        
        # Import and set the correct pipline
        import_string = f"""EFScanAlgo.{
                stage.name.lower()
            }_stage.{ 
                model_name 
            }""".strip('.py')
        
        # Try to import the module
        try:
            pipeline_module = importlib.import_module(import_string)
        except ImportError:
            import sys
            print(sys.path)
            raise ImportError(f"Could not import {import_string}")
        
        # Try to get the needed functions and definitions
        try:
            var = "DETECT_FUNCTION"
            self.__detect_func = getattr(pipeline_module, "detect")
            var = "INIT_PIPELINE_FUNCTION"
            init_pipeline_func = getattr(pipeline_module, "init_pipeline", None)
            var = "TARGET_STAGE"
            self.target_stage = getattr(pipeline_module, "TARGET_STAGE")
            var = "SINGLE_STAGE"
            self.single_stage = getattr(pipeline_module, "SINGLE_STAGE")
        except AttributeError:
            raise AttributeError(f"Could not find {var} in {import_string}")   

        # Get the relevant data
        if test_type == TestType.SIMUFSC:
            self.test_data = SimufscData
        elif test_type == TestType.SIMUENEM:
            raise NotImplementedError("SIMUENEM data not implemented yet")
            self.test_data = SimuenemData
        elif test_type == TestType.SIMULINHO:
            raise NotImplementedError("SIMULINHO data not implemented yet")
            self.test_data = SimulinhoData
        elif test_type == TestType.PS_ALUNOS:
            raise NotImplementedError("PS data not implemented yet")
            self.test_data = PSData
        else:
            raise ValueError("Invalid test type")
        
        # Calls init_pipeline if one exists
        if init_pipeline_func is not None:
            try:
                init_pipeline_func(self, self.config)
            except Exception as e:
                raise ValueError(f"Error while initializing pipeline: {e}")
            

    ## Main detect function ## 

    def detect(self, image : CoreImage):
        try:
            detections = self.__detect_func(self, image)
        except Exception as e:
            raise e
        
        return detections
