from api import CoreApi
from definitions.test_defs import TestType



# SECTION: Static constants

title_font = ("Helvetica", 13, "bold")
semititle_font = ("Helvetica", 11, "bold")



# SECTION: auxiliary classes

class Callback():
    def __init__(self):
        self.__callbacks = []

    def call(self):
        for callback in self.__callbacks:
            callback()

    def bind(self, callback):
        self.__callbacks.append(callback)


# SECTION: Config class

class Config:

    # Api instance
    api : CoreApi = CoreApi()

    # Callbacks
    folder_loaded_callback = Callback()
    
    # Non static global variables
    selected_test_type : TestType = TestType.PS_ALUNOS
    


