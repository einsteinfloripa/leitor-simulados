

# class EFscanAlgo:
    
#     __initialized = False
#     __scanner = None
#     def __init__(self, test_type : str, stage : str) -> None:
#         # Set path to import dynamically
#         if not self.__initialized:
#             self.__init_paths()
#         # Import Scanner class and create instance
#         from models.EFscanAlgo import get_scanner
#         self.__scanner = get_scanner('EFscanAlgo', "FIRST_STAGE.PY")

#     # Initialization function
#     def __init_paths(self):
#         import importlib
#         import sys
#         import pathlib
#         # Include the path to the root folder
#         path = pathlib.Path(__file__).parent.parent
#         sys.path.append(str(path))
#         # Include path to dsTools
#         self.__initialized = True

# EFscanAlgo('SIMUENEM', 'FIRST_STAGE.PY')