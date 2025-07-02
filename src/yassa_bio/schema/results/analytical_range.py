from __future__ import annotations
from pydantic import (
    Field,
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import SchemaModel


class AnalyticalRange(SchemaModel):
    lod: PositiveFloat = Field(
        ..., gt=0, description="Lower limit of detection for the assay."
    )
    loq: PositiveFloat | None = Field(
        None, gt=0, description="Lower limit of quantitation; must exceed LOD."
    )
    lower: PositiveFloat = Field(
        ..., gt=0, description="Lower bound of quantifiable range."
    )
    upper: PositiveFloat = Field(
        ..., gt=0, description="Upper bound of quantifiable range."
    )
    units: str = Field(
        ...,
        description=(
            "Units used for all concentration values in this range (e.g. 'ng/mL')."
        ),
        examples=["ng/mL", "pg/mL", "mU/mL", "IU/mL"],
    )

    @model_validator(mode="after")
    def _check_bounds(self):
        assert self.lower < self.upper, "lower must be < upper"
        if self.loq:
            assert self.lod < self.loq <= self.lower, "LOD < LOQ ≤ lower range"
        return self
