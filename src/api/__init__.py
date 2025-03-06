"""
This module is supposed to work as a kind pf backend api for the graphical
user interface.

I figured that it would be a good idea to separate the code in backend/frontend panoram
so that i can easily switch out the frontend to a more advanced GUI if needed
or a web based aplication.
"""

from .api import CoreApi
from .sync_channel import ProgressTracker

__all__ = ['CoreApi', 'ProgressTracker']