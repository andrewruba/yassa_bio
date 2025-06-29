from __future__ import annotations
from typing import Literal, List, Optional
from pydantic import Field

from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.core.model import StrictModel


class Plate(StrictModel):
    """One physical plate with its wells."""

    plate_id: str = Field(
        ...,
        description="Stable identifier: barcode, run name, or UUID.",
    )
    sheet_index: int = Field(
        0,
        ge=0,
        description=(
            "0-based sheet index when the raw file is a multi-sheet XLS/X. "
            "For CSV/TXT leave as 0."
        ),
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
