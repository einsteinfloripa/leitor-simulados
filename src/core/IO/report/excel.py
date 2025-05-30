from __future__ import annotations

from pathlib import Path
import pandas as pd

from core.IO import FileExtension
from core.IO.report import (
    ReportIO,
    ReportData,
) 

from utils.log import LoggingSystem

__all__ = ["DefaultEXCEL"]

class DefaultEXCEL(ReportIO):

    _logger = LoggingSystem.get_new_logger(__name__)

    @property
    def extension(self) -> FileExtension:
        return FileExtension.EXCEL

    def write(self, data: ReportData, fullpath: Path) -> bool:
        self._logger.info(f"Writing data to EXCEL file: {fullpath}")
        self._logger.debug(f"Data: {data}")

        data: pd.DataFrame = data.to_pandas()
        
        # Reset the index (moves index into a column)
        data = data.reset_index()

        # Change the name of the index column
        data = data.rename(columns={"index": "image"})

        # Write the DataFrame to CSV
        data.to_excel(fullpath, index=False)

        return True  # Ensure the function returns a boolean
