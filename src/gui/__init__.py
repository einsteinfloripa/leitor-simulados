from api import CoreApi

# Fonts
title_font = ("Helvetica", 13, "bold")
semititle_font = ("Helvetica", 11, "bold")

# Callback class
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
