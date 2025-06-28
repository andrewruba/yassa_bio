from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field
from yassa_bio.config.plate import Plate
from yassa_bio.config.standard import StandardSeries


class ElisaDataMap(BaseModel):
    """Top-level container passed into the analysis engine."""

    plates: List[Plate] = Field(..., description="One entry per physical plate.")
    standards: Optional[List[StandardSeries]] = Field(
        None,
        description="If not supplied, concentrations must be on each Well.",
    )


# validation. ie. if exclude, then exclude_reason must be set. well name should be a certain format "A1", "H12", units, etc.
