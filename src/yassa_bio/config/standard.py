from __future__ import annotations
from pydantic import BaseModel, Field


class StandardSeries(BaseModel):
    """Nominal concentrations for a serially diluted standard curve."""

    start_conc: float = Field(
        ...,
        description="Top standard concentration (C₀) in `units`.",
    )
    dilution_factor: float = Field(
        ...,
        description="Constant fold-dilution factor (e.g. 2 for 1:2).",
    )
    num_levels: int = Field(
        ...,
        description="Total number of standards prepared (≥ 2).",
    )
    units: str = Field(
        "ng/mL",
        description="Concentration units for the series.",
    )
