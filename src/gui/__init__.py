from api import CoreApi
from definitions.test_defs import TestType


# SECTION: Static constants

title_font = ("Helvetica", 13, "bold")
semititle_font = ("Helvetica", 11, "bold")
regular_font = ("Helvetica", 11)


# SECTION: auxiliary classes

class EventBus:

    # Subscribers
    _subscribers = {}

    # Subcribe Decorator
    @classmethod
    def subscribe(cls, callback, *events):        
        for event in events:
            if event not in cls._subscribers:
                cls._subscribers[event] = []
            cls._subscribers[event].append(callback)

    
    @classmethod
    def publish(cls, event, *args, **kwargs):
        """Publish an event to all subscribers"""
        for callback in cls._subscribers.get(event, []):
            callback(event, *args, **kwargs)



# SECTION: Config class

class Config:

    # Api instance
    api : CoreApi = CoreApi()

    # Non static global variables
    selected_test_type : TestType = TestType.PS_ALUNOS
    current_image_index : int = 0


