from __future__ import annotations
from typing import List
from pydantic import Field

from yassa_bio.core.model import SchemaModel

from yassa_bio.schema.layout.plate import Plate


class DataMap(SchemaModel):
    """Map of a tabular plate-reader export file to physical plates and wells."""

    plates: List[Plate] = Field(
        ..., description="One entry per physical plate in the raw file."
    )
