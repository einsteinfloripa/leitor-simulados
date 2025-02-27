import threading
from functools import wraps



class ProgressTracker:
    """A thread-safe queue for float progress updates."""
    def __init__(self):
        self._lock : threading.Lock = threading.Lock()
        self._procede_event : threading.Event = threading.Event()
        self._step = 0
        self._total_steps = -1
        self._running = True

    def _has_total_steps(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            if self._total_steps == -1:
                raise ValueError("Total steps has not been set.")
            return func(*args, **kwargs)
        return wrapper

    def set_total_steps(self, total_steps: int) -> None:
        """Set the total number of steps."""
        with self._lock:
            self._total_steps = total_steps
    
    @_has_total_steps
    def increment(self, n=1) -> None:
        """Increment the current progress."""
        with self._lock:
            self._step += n
            self._procede_event.set()            
    
    @_has_total_steps
    def get_step(self) -> int:
        """Retrieve the current progress step."""
        self._procede_event.wait()
        with self._lock:
            self._procede_event.clear()
            return self._step

    def set_finished(self) -> None:
        """Set the progress as finished."""
        with self._lock:
            self._current_progress = 1.0
    
    def is_finished(self) -> bool:
        """Set the progress as finished."""
        return self._step == self._total_steps
    
    def is_zero(self) -> bool:
        """Reset the progress to 0."""
        with self._lock:
            return self._step == 0

    def shutdown(self) -> None:
        """Shutdown the progress tracker."""
        with self._lock:
            self._running = False
    
    def running(self) -> bool:
        """Check if the progress tracker is running."""
        with self._lock:
            return self._running