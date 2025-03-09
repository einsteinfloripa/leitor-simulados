import sys
import logging
import logging.handlers
import queue
import threading
import inspect
from collections import deque
from typing import List, Generator
from functools import wraps


TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

class CustomFormatter(logging.Formatter):
    """Custom logging formatter."""
    def format(self, record):
        return f"[{self.formatTime(record)}] [{record.levelname:^8}] {record.name:^15} - {record.getMessage()}"

class CircularLogHandler(logging.Handler):
    """Circular buffer log handler with built-in QueueHandler support."""
    def __init__(self, max_logs: int = 10000):
        super().__init__()
        self.log_buffer = deque(maxlen=max_logs)  # Circular buffer

    def emit(self, record: logging.LogRecord):
        """Store log record message."""
        log_entry = self.format(record)
        self.log_buffer.append(log_entry)

    def get_logs(self) -> List[str]:
        """Retrieve and clear logs."""
        logs = list(self.log_buffer)
        self.log_buffer.clear()
        return logs


class QueueHandler(logging.handlers.QueueHandler):

    def __init__(self, *args, **kwds):
        self._event : threading.Event = kwds.pop("event")
        return super().__init__(*args, **kwds)

    def emit(self, record):
        try:
            self.enqueue(self.prepare(record))
            self._event.set()
        except Exception:
            self.handleError(record)


class LoggingSystem:
    """Centralized logging system using QueueHandler and QueueListener."""

    _base_logger = logging.getLogger("base_circular_logger")
    

    @classmethod
    def initilize(cls, log_level):

        # Sync tools
        cls._lock = threading.Lock()
        cls._new_logs = threading.Event()

        # Flags
        cls._alive = True
        cls._active_listener = False

        # Aux structs
        cls._log_queue = queue.Queue()  # Log queue
        
        # Formatter
        cls._formatter = CustomFormatter()
                    
        # Handlers
        # Circular buffer handler
        cls._circular_handler = CircularLogHandler(max_logs=4)
        cls._circular_handler.setFormatter(cls._formatter)
        # Queue handler
        cls._queue_handler = QueueHandler(cls._log_queue, event=cls._new_logs)
        # Sys handler
        cls._sys_handler = logging.StreamHandler(sys.stderr)
        cls._sys_handler.setFormatter(cls._formatter)

        # Logger
        if log_level is None:
            cls._base_logger.addHandler(logging.NullHandler())
        else:
            # Set log level
            if log_level == "TRACE":
                log_level = 5
            cls._base_logger.setLevel(log_level)
            print(f"Log level set to {log_level}")

            # Listener
            cls._queue_listener = logging.handlers.QueueListener(
                cls._log_queue, cls._circular_handler, cls._sys_handler
            )
            cls._base_logger.addHandler(cls._queue_handler)
            
            cls._queue_listener.start()  # Start listening in a separate thread
    
    @classmethod
    def shutdown(cls):
        """Shutdown the logging system."""
        cls._alive = False
        cls._new_logs.set()
        try:
            cls._queue_listener.stop()
        except AttributeError:
            pass
    
    @classmethod
    def get_new_logger(cls, name):
        """Returns a child logger."""
        new_logger = cls._base_logger.getChild(name)
        new_logger.name = new_logger.name.replace("base_circular_logger.", "")
        return new_logger

    @classmethod
    def get_logs(cls) -> List[str]:
        """Retrieve logs from circular buffer."""
        return cls._circular_handler.get_logs()

    @classmethod
    def listen(cls) -> Generator[str, None, None]:
        """Yield log entries in real time."""

        with cls._lock:
            if cls._active_listener:
                raise RuntimeError("Only one listener can be active at a time.")
            else:
                cls._active_listener = True
            
        while cls._alive:
            # Wait for new logs
            cls._new_logs.wait()

            # Get the new logs
            cls._circular_handler.acquire()
            new_logs = cls._circular_handler.get_logs()
            cls._circular_handler.release()
            
            # Yield the new logs
            for log_entry in new_logs:
                yield log_entry
            
            cls._new_logs.clear()

        cls._active_listener = False


###################################################################################
# Decorator helper to log method calls
###################################################################################

    @classmethod
    def trace_methods(
            cls, 
            logger: logging.Logger,
            log_level : int | str ="TRACE",
            header = None,
            footer = None
        ):
        """Class decorator to log execution of all methods in a class"""
        
        if header is not None:
            header_txt = f'{"-"*30} [{header}] {"-"*30}'
        if footer is not None:
            footer_txt = f'{"-"*30} [{footer}] {"-"*30}'

        if not isinstance(log_level, int):
            if log_level.upper() == "TRACE":
                log_level = 5
            else:
                log_level = getattr(logging, log_level.upper(), logging.DEBUG)  # Convert log level string to int


        def decorator(target_cls):
            # Only process attributes defined directly in the class dictionary
            for attr_name, attr_value in target_cls.__dict__.items():
                # Skip magic methods, non-callables, properties, and special attributes
                if (
                    attr_name.startswith("__") or 
                    not callable(attr_value) or 
                    inspect.isclass(attr_value)
                ):
                    continue
                    
                original_method = attr_value
                if target_cls.__name__ == "Detection":
                    print(f"Processing method {attr_name}")
                
                # Create a closure that captures the correct method and name
                def make_wrapper(method_name, method):
                    @wraps(method)
                    def wrapper(*args, **kwargs):
                        if header is not None:
                            logger.log(log_level, header_txt)
                        logger.log(log_level, f"[{target_cls.__name__}.{method_name}] called with args={args}, kwargs={kwargs}")
                        
                        result = method(*args, **kwargs)  # Call the original method
                        
                        logger.log(log_level, f"[{target_cls.__name__}.{method_name}] return value = {result}")
                        if footer is not None:
                            logger.log(log_level, footer_txt)
                        return result
                    return wrapper
                
                wrapper = make_wrapper(attr_name, original_method)
                
                # Preserve static and class methods
                if isinstance(original_method, staticmethod):
                    setattr(target_cls, attr_name, staticmethod(wrapper))
                elif isinstance(original_method, classmethod):
                    setattr(target_cls, attr_name, classmethod(wrapper))
                else:
                    setattr(target_cls, attr_name, wrapper)
                    
            return target_cls
        
        return decorator
