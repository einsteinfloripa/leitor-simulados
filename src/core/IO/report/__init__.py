"""
This module is intended to provide customizable functions to
export the final report of the answers to different formats.
"""

# Definitions
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from abc import abstractmethod
from functools import wraps
from pathlib import Path

from core.definitions import TestType
from core.definitions.question import TestQuestions

from ..base import Exporter
from .. import FileExtension

# SECTION: data structures

@dataclass
class ReportData:
    test_type : TestType = TestType.NULL
    names : list[str] = field(default_factory=list)
    test_questions : list[TestQuestions] = field(default_factory=list)



# SECTION: Base report exporter class

class ReportIO(Exporter):
    """
    Base class for exporting the final report of the answers.
    """

    _registry: dict[str, ReportIO] = {}

    ## Factory method ##
    @classmethod
    def get_by_name(cls, exporter_name: str) -> ReportIO:
        """Factory method to create an exporter."""
        if exporter_name not in cls._registry:
            raise ValueError(f"Exporter {exporter_name} not found")
        return cls._registry[exporter_name]
    

    ## Initialization ##
    def __init_subclass__(cls):
        """Automatically register subclasses."""
        # Check if the subclass has the ex
        if not hasattr(cls, "extension"):
            raise ValueError("Subclasses must have a extension attribute")
        ReportIO._registry[cls.__name__] = cls()


    ## Getters and setters ##
    @classmethod
    def get_available_formats(cls) -> dict[str : FileExtension]:
        """Return all registered export formats."""
        return {name: cls.extension for name, cls in cls._registry.items()}
    


    ## Main abstract method ##
    @abstractmethod
    def write(self, data_struc : ReportData, fullpath : Path) -> bool:
        """
        Method that must be implemented by all exporters.
        
        This method should receive a ReportData object and write
        the data to a file in the format of the exporter.

        The return value should be True if the operation was successful,
        and False otherwise.
        """
        pass


    ## Tool methods for subclasses ##    
    @classmethod
    def get_config(cls) -> dict:
        """Return the configuration of the exporter."""
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return {'config': {'date': now}}


    ## Decorators ##
    @classmethod
    def assert_data(cls, func):
        @wraps(func)
        def wrapper(self, data: ReportData, fullpath: str):
            # Assert right data structure
            assert isinstance(data, ReportData), \
                "The data must be a ReportData object"
            # Assert right variables
            assert isinstance(data.test_type, TestType), \
                "The test type must be a TestType object"
            assert data.test_type is not TestType.NULL, \
                "The test type must be a valid TestType object"
            # Assert has quastions and names
            assert len(data.names) > 0, \
                "The names list must have at least one name"
            assert len(data.names) == len(data.test_questions), \
                "The number of names and test questions must be the same"
            # Assert right fullpath
            assert fullpath.endswith(self.extension.value), \
                f"The fullpath must have the extension {self.extension}"
            return func(self, data, fullpath)
        return wrapper



# SECTION: concrete classes imports

from .json import DefaultJSON
from .csv import DefaultCSV