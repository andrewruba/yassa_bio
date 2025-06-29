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
    lod: PositiveFloat = Field(..., gt=0)
    loq: PositiveFloat | None = Field(None, gt=0)
    lower: PositiveFloat = Field(..., gt=0)
    upper: PositiveFloat = Field(..., gt=0)
    units: str = "ng/mL"

    @model_validator(mode="after")
    def _check_bounds(self):
        assert self.lower < self.upper, "lower must be < upper"
        if self.loq:
            assert self.lod < self.loq <= self.lower, "LOD < LOQ ≤ lower range"
        return self


class ReplicateCriteria(SchemaModel):
    max_cv_percent: PositiveFloat = Percent(10.0, lo=1, hi=50)


class QcSpec(SchemaModel):
    level: QcLevel
    tol_pct: tuple[PositiveFloat, PositiveFloat] = (
        Percent(80, lo=0, hi=200),
        Percent(120, lo=0, hi=200),
    )

    @model_validator(mode="after")
    def _check_window(self):
        lo, hi = self.tol_pct
        if lo >= hi:
            raise ValueError("tol_pct lower bound must be < upper bound")
        return self


class LinearityRules(SchemaModel):
    r_squared_min: PositiveFloat = Fraction01(0.98, description="0–1")
    per_level_acc_pct: PositiveFloat = Percent(15.0, lo=5, hi=50)
    min_levels_pass: PositiveFloat = Fraction01(0.75)

    @model_validator(mode="after")
    def _range_check(self):
        if not (0 < self.min_levels_pass <= 1):
            raise ValueError("min_levels_pass must be in (0,1]")
        return self


class DilutionLinearity(SchemaModel):
    max_bias_pct: PositiveFloat = Percent(20.0, lo=5, hi=50)
    max_cv_pct: PositiveFloat = Percent(20.0, lo=5, hi=50)
    min_levels: int = Field(3, ge=3, le=8)
    series_required: int = Field(3, ge=1, le=10)

    @model_validator(mode="after")
    def _positive_ints(self):
        if self.min_levels < 3:
            raise ValueError("min_levels must be ≥ 3")
        if self.series_required < 1:
            raise ValueError("series_required must be ≥ 1")
        return self


class HookEffectCheck(SchemaModel):
    threshold_pct_of_undiluted: PositiveFloat = Percent(80.0, lo=50, hi=100)


class TotalErrorRule(SchemaModel):
    overall_pct: PositiveFloat = Percent(30.0, lo=5, hi=100)
    loq_pct: PositiveFloat = Percent(40.0, lo=5, hi=100)


class QCSpec(SchemaModel):
    duplicate_cv: ReplicateCriteria = ReplicateCriteria()
    bands: List[QcSpec] = [QcSpec(level=QcLevel.ALL)]
    standards_nominal: List[PositiveFloat] | None = None  # Std‑0 … Std‑N
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    analytical_range: AnalyticalRange | None = None
