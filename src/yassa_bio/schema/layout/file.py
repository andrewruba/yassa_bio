from __future__ import annotations
from typing import Optional
from pydantic import Field, field_validator
from datetime import datetime
from pathlib import Path

from yassa_bio.core.model import SchemaModel
from yassa_bio.io.utils import as_path


class FileRef(SchemaModel):
    path: Path = Field(
        ...,
        description="Full path to the file on disk or cloud storage.",
    )

    @field_validator("path", mode="before")
    @classmethod
    def _norm_path(cls, v):
        if v is None:
            raise ValueError("path cannot be None")
        return as_path(v)


class PlateReaderFile(FileRef):
    """
    One export file coming off a plate reader.

    A *file* can hold data for one plate (common for csv / txt) or for many
    plates (multi-sheet XLS/X, some instrument binaries).  Nothing here is
    assay-specific – it’s purely where the raw numbers live.
    """

    run_date: Optional[datetime] = Field(
        None,
        description="Acquisition date/time if known.",
    )
    instrument: Optional[str] = Field(
        None,
        description="e.g. 'SpectraMax iD5' or reader serial number.",
    )
    operator: Optional[str] = Field(
        None,
        description="Initials or user ID of analyst.",
    )
