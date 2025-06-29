from __future__ import annotations
from typing import List, Optional
from pydantic import (
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.layout.enum import QcLevel


class AnalyticalRange(SchemaModel):
    lod: PositiveFloat
    loq: Optional[PositiveFloat] = None
    lower: PositiveFloat
    upper: PositiveFloat
    units: str = "ng/mL"

    @model_validator(mode="after")
    def _check_bounds(self):
        assert self.lower < self.upper, "lower must be < upper"
        if self.loq:
            assert self.lod < self.loq <= self.lower, "LOD < LOQ ≤ lower range"
        return self


class ReplicateCriteria(SchemaModel):
    max_cv_percent: PositiveFloat = 10.0


class QcSpec(SchemaModel):
    level: QcLevel
    tol_pct: tuple[PositiveFloat, PositiveFloat] = (80, 120)

    @model_validator(mode="after")
    def _check_window(self):
        lo, hi = self.tol_pct
        if lo >= hi:
            raise ValueError("tol_pct lower bound must be < upper bound")
        return self


class LinearityRules(SchemaModel):
    r_squared_min: PositiveFloat = 0.98
    per_level_acc_pct: PositiveFloat = 15.0
    min_levels_pass: PositiveFloat = 0.75  # fraction (0‑1)

    @model_validator(mode="after")
    def _range_check(self):
        if not (0 < self.min_levels_pass <= 1):
            raise ValueError("min_levels_pass must be in (0,1]")
        return self


class DilutionLinearity(SchemaModel):
    max_bias_pct: PositiveFloat = 20.0
    max_cv_pct: PositiveFloat = 20.0
    min_levels: int = 3
    series_required: int = 3

    @model_validator(mode="after")
    def _positive_ints(self):
        if self.min_levels < 3:
            raise ValueError("min_levels must be ≥ 3")
        if self.series_required < 1:
            raise ValueError("series_required must be ≥ 1")
        return self


class HookEffectCheck(SchemaModel):
    threshold_pct_of_undiluted: PositiveFloat = 80.0


class TotalErrorRule(SchemaModel):
    overall_pct: PositiveFloat = 30.0
    loq_pct: PositiveFloat = 40.0


class QCSpec(SchemaModel):
    duplicate_cv: ReplicateCriteria = ReplicateCriteria()
    bands: List[QcSpec] = [QcSpec(level=QcLevel.ALL)]
    standards_nominal: List[PositiveFloat] | None = None  # Std‑0 … Std‑N
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    analytical_range: AnalyticalRange | None = None
