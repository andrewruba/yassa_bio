from __future__ import annotations
from pydantic import Field

from yassa_bio.core.models import StrictModel


class StandardSeries(StrictModel):
    """Nominal concentrations for a serially diluted standard curve."""

    start_concentration: float = Field(
        ...,
        description="Top standard concentration (C₀) in `units`.",
    )
    dilution_factor: float = Field(
        ...,
        description="Constant fold-dilution factor (e.g. 2 for 1:2).",
    )
    num_levels: int = Field(
        ...,
        ge=2,
        description="Total number of standards prepared (≥ 2).",
    )
    concentration_units: str = Field(
        "ng/mL",
        description="Concentration units for the series.",
        examples=["ng/mL", "pg/mL", "mU/mL", "IU/mL"],
    )
