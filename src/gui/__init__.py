from api import CoreApi

class Callback():
    def __init__(self):
        self.__callbacks = []

    def call(self):
        for callback in self.__callbacks:
            callback()

    def bind(self, callback):
        self.__callbacks.append(callback)


folder_loaded_callback = Callback()
api_instance : CoreApi = CoreApi()
