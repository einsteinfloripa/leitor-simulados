import inspect
from enum import Enum
from collections import defaultdict

__all__ = ['EventBus', 'Calltime']

class Calltime(Enum):
    """
    Enumeration representing the execution timing of event subscribers.
    
    Attributes
    ----------
    EARLY : int
        Represents early execution (value 0).
    DEFAULT : int
        Represents default execution timing (value 1).
    LATE : int
        Represents late execution (value 2).
    """
    EARLY = 0
    DEFAULT = 1
    LATE = 2


class FunctionRegistry:
    """
    A registry to store and manage functions and methods associated with classes.
    """
    
    def __init__(self):
        """
        Initializes the function registry.
        """
        self.data = {}

    def add_class(self, class_name, methods):
        """
        Stores the methods of a class in the registry.
        
        Parameters
        ----------
        class_name : str
            The name of the class.
        methods : list of tuple
            A list of tuples where each tuple contains a method name and the method itself.
        """
        self.data[class_name] = {name: method for name, method in methods}

    def bind_methods(self, class_name, instance):
        """
        Binds stored methods to an instance, properly handling static and class methods.
        
        Parameters
        ----------
        class_name : str
            The name of the class whose methods are being bound.
        instance : object
            The instance of the class to which the methods should be bound.
        """
        bound_methods = {}
        cls = instance.__class__
        for name, method in self.data[class_name].items():
            if isinstance(method, staticmethod):
                bound_methods[name] = method
            elif isinstance(method, classmethod):
                bound_methods[name] = method.__get__(None, cls)
            else:
                bound_methods[name] = method.__get__(instance, cls)
        self.data[class_name] = bound_methods

    def get_bound_method(self, fullname):
        """
        Retrieves a bound method by its fully qualified name.
        
        Parameters
        ----------
        fullname : str
            The fully qualified name of the method (e.g., 'ClassName.method_name').
        
        Returns
        -------
        function
            The bound method.
        """
        class_name, method_name = fullname.split('.')
        return self.data[class_name][method_name]


class EventBus:
    """
    A event bus that allows subscribing to and publishing events.
    
    Attributes
    ----------
    registry : FunctionRegistry
        A registry for storing function references.
    _subscribers : defaultdict
        A dictionary mapping event names to lists of (method_name, calltime) tuples.
    """
    registry = FunctionRegistry()
    _subscribers = defaultdict(list)
    
    @classmethod
    def bind(cls, target_cls):
        """
        Binds a class to the event bus by registering its methods and overriding `__init__`.
        Every class that wants to use the event bus should be decorated with this method.

        example:
        @EventBus.bind
        class MyClass:
            @EventBus.subscribe("event_name")
            def on_event(self, event_name, *args, **kwargs):
                pass
        
        Parameters
        ----------
        target_cls : type
            The class whose methods should be registered with the event bus.
        
        Returns
        -------
        type
            The same class, now modified to support automatic event binding.
        """
        # Save all methods of the class in the registry
        methods = [
            (name, method) for name, method in target_cls.__dict__.items()
            if inspect.isfunction(method) or isinstance(method, (staticmethod, classmethod))
        ]
        cls.registry.add_class(target_cls.__name__, methods)

        # Redefine the init method to bind the methods to the instance
        original_init = target_cls.__init__
        
        def new_init(self, *args, **kwargs):
            """
            Overrides the class constructor to automatically bind event-handling methods.
            """
            original_init(self, *args, **kwargs)
            cls.registry.bind_methods(self.__class__.__name__, self)
        
        target_cls.__init__ = new_init
        return target_cls

    @classmethod
    def subscribe(cls, *event_names, calltime=Calltime.DEFAULT):
        """
        Decorator to register a method as an event subscriber.
        
        Parameters
        ----------
        *event_names : str
            One or more event names to subscribe to.
        calltime : Calltime, optional
            Determines when the method is triggered relative to other subscribers (default is Calltime.DEFAULT).
        
        Returns
        -------
        function
            The original function, unchanged.
        """
        def decorator(func):
            fullname = func.__qualname__
            for event_name in event_names:
                cls._subscribers[event_name].append((fullname, calltime))
            return func
        return decorator

    @classmethod
    def publish(cls, event_name, *args, **kwargs):
        """
        Publishes an event, triggering all subscribed methods in the specified order.
        
        Parameters
        ----------
        event_name : str
            The name of the event to trigger.
        *args : tuple
            Positional arguments to pass to the subscribed methods.
        **kwargs : dict
            Keyword arguments to pass to the subscribed methods.
        """
        sorted_subscribers = sorted(
            cls._subscribers.get(event_name, []),
            key=lambda x: x[1].value  # Sort by Calltime value (EARLY, DEFAULT, LATE)
        )
        for fullname, _ in sorted_subscribers:
            bound_method = cls.registry.get_bound_method(fullname)
            bound_method(event_name, *args, **kwargs)
