from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PlateReaderFile(BaseModel):
    """Pointer to a raw plate-reader export on disk, S3, GCS, etc."""

    filepath: Optional[str] = Field(
        None,
        description=(
            "Full path to the file on disk or cloud storage. "
            "Used as the lookup key. "
            "If None, filename is used as the key."
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
