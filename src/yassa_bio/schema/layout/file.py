from __future__ import annotations
from typing import Optional
from pydantic import Field
from datetime import datetime

from yassa_bio.core.model import SchemaModel


class PlateReaderFile(SchemaModel):
    """
    Metadata for one *physical export file* coming off a plate reader.
    A file may contain data for one or many plates.
    """

    filepath: str = Field(
        ...,
        description=(
            "Full path to the file on disk or cloud storage. Used as the lookup key."
        ),
    )
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
