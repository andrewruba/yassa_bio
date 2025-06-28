from __future__ import annotations
from pydantic import BaseModel, Field


class StandardSeries(BaseModel):
    start_conc: float = Field(..., description="C₀ (highest standard) in `units`.")
    dilution_factor: float = Field(..., description="d > 1 (e.g. 2 for 1:2).")
    num_levels: int = Field(..., description="Total standards prepared (≥ 2).")
    units: str = "ng/mL"
