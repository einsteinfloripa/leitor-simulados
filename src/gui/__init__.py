from api import CoreApi
from core.definitions.test_defs import TestType


# =============================================================================
# Static Constants
# =============================================================================

title_font = ("Helvetica", 13, "bold")
semititle_font = ("Helvetica", 11, "bold")
regular_font = ("Helvetica", 11)


# =============================================================================
# Auxiliary Classes
# =============================================================================

class EventBus:
    """
    A simple event bus for subscribing and publishing events within the application.

    This class provides a publish/subscribe mechanism that enables decoupled communication
    between different components of the application.
    """

    # Dictionary to hold subscribers for each event
    _subscribers = {}

    @classmethod
    def subscribe(cls, callback, *events):
        """
        Subscribe a callback function to one or more events.

        Parameters
        ----------
        callback : callable
            The function to be called when the event is published.
        *events : str
            One or more event names to subscribe to.
        """
        for event in events:
            if event not in cls._subscribers:
                cls._subscribers[event] = []
            cls._subscribers[event].append(callback)

    @classmethod
    def publish(cls, event, *args, **kwargs):
        """
        Publish an event to all subscribed callback functions.

        Parameters
        ----------
        event : str
            The name of the event to publish.
        *args : tuple
            Positional arguments to pass to the callback functions.
        **kwargs : dict
            Keyword arguments to pass to the callback functions.
        """
        for callback in cls._subscribers.get(event, []):
            callback(event, *args, **kwargs)


# =============================================================================
# Configuration Class
# =============================================================================

class Config:
    """
    Global configuration class holding static and dynamic variables for the application.

    Attributes
    ----------
    api : CoreApi
        An instance of the CoreApi.
    selected_test_type : TestType
        The currently selected test type.
    current_image_index : int
        The index of the currently selected image.
    """

    # Static API instance
    api: CoreApi = CoreApi()

    # Global dynamic variables
    selected_test_type: TestType = TestType.PS_ALUNOS
    current_image_index: int = 0
