from __future__ import annotations
from typing import Literal, List
from pydantic import BaseModel, Optional, Field
from yassa_bio.config.file import FileRef
from yassa_bio.config.well import Well
from datetime import datetime


class Plate(BaseModel):
    """One physical plate plus its originating data file with metadata."""

    plate_id: str = Field(
        ...,
        description="Stable identifier: barcode, run name, or UUID.",
    )
    file: FileRef
    plate_format: Literal[96, 384, 1536] = Field(
        96,
        description="Well count of the plate (default 96).",
    )
    wells: List[Well]

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
