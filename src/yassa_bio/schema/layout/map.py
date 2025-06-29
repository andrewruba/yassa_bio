from __future__ import annotations
from typing import List
from pydantic import Field

from yassa_bio.core.model import StrictModel

from yassa_bio.schema.layout.plate import Plate


class DataMap(StrictModel):
    """Map of a tabular plate-reader export file to physical plates and wells."""

    plates: List[Plate] = Field(
        ..., description="One entry per physical plate in the raw file."
    )
