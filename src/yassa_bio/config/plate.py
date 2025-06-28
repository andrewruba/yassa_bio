from __future__ import annotations
from typing import Literal, List, Optional
from pydantic import BaseModel, Field
from yassa_bio.config.well import Well
from yassa_bio.config.standard import StandardSeries


class Plate(BaseModel):
    """One physical plate with its wells."""

    plate_id: str = Field(
        ...,
        description="Stable identifier: barcode, run name, or UUID.",
    )
    plate_format: Literal[96, 384, 1536] = Field(
        96,
        description="Well count of the plate (default 96).",
    )
    wells: List[Well]
    standards: Optional[StandardSeries] = Field(
        None,
        description="If not supplied, concentrations must be on each Well.",
    )
