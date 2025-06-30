from __future__ import annotations
from typing import List
from pydantic import (
    Field,
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.layout.enum import QcLevel
from yassa_bio.core.typing import Percent, Fraction01


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
        description="Units used for all concentration values in this range (e.g. 'ng/mL').",
        examples=["ng/mL", "pg/mL", "mU/mL", "IU/mL"],
    )

    @model_validator(mode="after")
    def _check_bounds(self):
        assert self.lower < self.upper, "lower must be < upper"
        if self.loq:
            assert self.lod < self.loq <= self.lower, "LOD < LOQ ≤ lower range"
        return self


class ReplicateCriteria(SchemaModel):
    max_cv_percent: PositiveFloat = Percent(
        10.0, lo=1, hi=50, description="Maximum allowed CV (%) across replicate wells."
    )


class QcSpec(SchemaModel):
    level: QcLevel = Field(..., description="QC band label this spec applies to.")
    tol_pct: tuple[PositiveFloat, PositiveFloat] = (
        Percent(80, lo=0, hi=200, description="Lower recovery limit (%)."),
        Percent(120, lo=0, hi=200, description="Upper recovery limit (%)."),
    )

    @model_validator(mode="after")
    def _check_window(self):
        lo, hi = self.tol_pct
        if lo >= hi:
            raise ValueError("tol_pct lower bound must be < upper bound")
        return self


class LinearityRules(SchemaModel):
    r_squared_min: PositiveFloat = Fraction01(
        0.98, description="Minimum acceptable R² for the linearity fit."
    )
    per_level_acc_pct: PositiveFloat = Percent(
        15.0, lo=5, hi=50, description="Accuracy threshold (%) required at each level."
    )
    min_levels_pass: PositiveFloat = Fraction01(
        0.75, description="Fraction of levels that must pass accuracy check."
    )


class DilutionLinearity(SchemaModel):
    max_bias_pct: PositiveFloat = Percent(
        20.0, lo=5, hi=50, description="Maximum allowed bias (%) after dilution."
    )
    max_cv_pct: PositiveFloat = Percent(
        20.0,
        lo=5,
        hi=50,
        description="Maximum allowed CV (%) across dilution replicates.",
    )
    min_levels: int = Field(
        3, ge=3, le=8, description="Minimum number of dilution levels to evaluate."
    )
    series_required: int = Field(
        3, ge=1, le=10, description="Number of replicate dilution series required."
    )


class HookEffectCheck(SchemaModel):
    threshold_pct_of_undiluted: PositiveFloat = Percent(
        80.0,
        lo=50,
        hi=100,
        description="Minimum response (%) of undiluted sample required to pass.",
    )


class TotalErrorRule(SchemaModel):
    overall_pct: PositiveFloat = Percent(
        30.0,
        lo=5,
        hi=100,
        description="Total error threshold (%) for all quantifiable samples.",
    )
    loq_pct: PositiveFloat = Percent(
        40.0, lo=5, hi=100, description="Total error threshold (%) specifically at LOQ."
    )


class QCSpec(SchemaModel):
    duplicate_cv: ReplicateCriteria = ReplicateCriteria()
    bands: List[QcSpec] = [QcSpec(level=QcLevel.ALL)]
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    analytical_range: AnalyticalRange | None = Field(
        None,
        description="Overall dynamic range and quantitation thresholds of the assay.",
    )
