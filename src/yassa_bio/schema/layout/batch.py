from __future__ import annotations
from typing import List
from pydantic import Field

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.layout.plate import PlateData


class BatchData(SchemaModel):
    """
    A *batch* = collection of plates whose data are evaluated together.

    Typical uses
    ────────────
    • **Validation batch** – one plate (or a set of plates read together) that
      targets a single validation exercise: carry-over, stability, etc.
    • **Routine run** – multiple plates from the same study day that share
      a calibration curve / QC bracket.
    """

    plates: List[PlateData] = Field(
        ..., description="All plates whose results will be combined for acceptance."
    )
