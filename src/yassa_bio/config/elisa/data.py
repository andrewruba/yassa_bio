from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel
from yassa_bio.config.plate import Plate
from yassa_bio.config.standard import StandardSeries


class ElisaDataMap(BaseModel):
    plates: List[Plate]
    standards: Optional[List[StandardSeries]] = None


# validation. ie. if exclude, then exclude_reason must be set. well name should be a certain format "A1", "H12", etc.
# descriptions for all fields
