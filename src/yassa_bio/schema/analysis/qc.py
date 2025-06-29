from __future__ import annotations
from typing import List, Optional
from pydantic import (
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import StrictModel


class AnalyticalRange(StrictModel):
    lod: PositiveFloat
    loq: Optional[PositiveFloat] = None
    lower: PositiveFloat
    upper: PositiveFloat
    units: str = "ng/mL"

    # cross‑field sanity
    @model_validator(mode="after")
    def _check_bounds(self):
        assert self.lower < self.upper, "lower must be < upper"
        if self.loq:
            assert self.lod < self.loq <= self.lower, "LOD < LOQ ≤ lower range"
        return self


class DuplicateCriteria(StrictModel):
    max_cv_percent: PositiveFloat = 10.0


class ControlWindow(StrictModel):
    qc_id: str
    min_value: PositiveFloat
    max_value: PositiveFloat
    units: str = "ng/mL"


class SpikeRecovery(StrictModel):
    spike_id: str
    added_conc: PositiveFloat
    target_recovery_pct: tuple[PositiveFloat, PositiveFloat] = (80.0, 120.0)
    units: str = "ng/mL"


class LinearityRules(StrictModel):
    r_squared_min: PositiveFloat = 0.98
    per_level_acc_pct: PositiveFloat = 15.0
    min_levels_pass: PositiveFloat = 0.75  # fraction (0‑1)


class DilutionLinearity(StrictModel):
    max_bias_pct: PositiveFloat = 20.0
    max_cv_pct: PositiveFloat = 20.0
    min_levels: int = 3


class HookEffectCheck(StrictModel):
    threshold_pct_of_undiluted: PositiveFloat = 80.0


class TotalErrorRule(StrictModel):
    overall_pct: PositiveFloat = 30.0
    loq_pct: PositiveFloat = 40.0


class QCSpec(StrictModel):
    duplicate_cv: DuplicateCriteria = DuplicateCriteria()
    controls: List[ControlWindow] = []  # kit or in‑house QCs
    spikes: List[SpikeRecovery] = []
    standards_nominal: List[PositiveFloat] | None = None  # Std‑0 … Std‑N
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    analytical_range: AnalyticalRange | None = None
