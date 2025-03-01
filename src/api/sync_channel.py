import threading
from functools import wraps

class ProgressTracker:
    """
    A thread-safe progress tracker for managing and monitoring progress updates.
    
    Attributes
    ----------
    _lock : threading.Lock
        Ensures thread-safe access to shared data.
    _procede_event : threading.Event
        Synchronizes progress retrieval.
    _step : int
        Tracks the current step in progress.
    _total_steps : int
        Defines the total number of steps (-1 if not set).
    _running : bool
        Indicates if the tracker is active.
    """
    
    def __init__(self):
        """
        Initializes a new ProgressTracker instance with default values.
        """
        self._lock: threading.Lock = threading.Lock()
        self._procede_event: threading.Event = threading.Event()
        self._step = 0
        self._total_steps = -1
        self._running = True

    def _has_total_steps(func):
        """
        Decorator to ensure that total steps are set before calling a method.

        Parameters
        ----------
        func : callable
            The function to wrap.

        Returns
        -------
        callable
            The wrapped function.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            if self._total_steps == -1:
                raise ValueError("Total steps has not been set.")
            return func(*args, **kwargs)
        return wrapper

    def set_total_steps(self, total_steps: int) -> None:
        """
        Set the total number of steps.

        Parameters
        ----------
        total_steps : int
            The total number of steps in the progress tracker.
        """
        with self._lock:
            self._total_steps = total_steps
    
    @_has_total_steps
    def increment(self, n: int = 1) -> None:
        """
        Increment the current progress by a given number of steps.

        Parameters
        ----------
        n : int, optional
            The number of steps to increment (default is 1).
        """
        with self._lock:
            self._step += n
            self._procede_event.set()
    
    @_has_total_steps
    def get_step(self) -> int:
        """
        Retrieve the current progress step.

        Returns
        -------
        int
            The current step count.
        """
        self._procede_event.wait()
        with self._lock:
            self._procede_event.clear()
            return self._step

    def set_finished(self) -> None:
        """
        Mark the progress tracker as finished by setting the step count to total steps.
        """
        with self._lock:
            self._step = self._total_steps
    
    def is_finished(self) -> bool:
        """
        Check if the progress tracker has reached the total steps.

        Returns
        -------
        bool
            True if the tracker has reached the total steps, False otherwise.
        """
        with self._lock:
            return self._step == self._total_steps
    
    def is_zero(self) -> bool:
        """
        Check if the progress is at the initial state (zero steps completed).

        Returns
        -------
        bool
            True if the progress is zero, False otherwise.
        """
        with self._lock:
            return self._step == 0

    def shutdown(self) -> None:
        """
        Shut down the progress tracker.
        """
        with self._lock:
            self._running = False
    
    def running(self) -> bool:
        """
        Check if the progress tracker is currently running.

        Returns
        -------
        bool
            True if the tracker is running, False otherwise.
        """
        with self._lock:
            return self._running
