from __future__ import annotations
from typing import List, Optional
from pydantic import Field

from yassa_bio.schema.layout.enum import PlateFormat
from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.core.model import SchemaModel


class Plate(SchemaModel):
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
    plate_format: PlateFormat = Field(
        default=PlateFormat.FMT_96,
        description="Well count of the plate.",
    )
    wells: List[Well]
    standards: Optional[StandardSeries] = Field(
        None,
        description="If not supplied, concentrations must be on each Well.",
    )
