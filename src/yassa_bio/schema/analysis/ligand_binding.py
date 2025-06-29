from __future__ import annotations
from typing import List, Optional, Literal

from pydantic import (
    BaseModel,
    PositiveFloat,
    model_validator,
)

# ────────────────────── enums ──────────────────────
CurveModel = Literal["4PL", "5PL", "linear"]
PotencyMethod = Literal["parallel_line", "ec50_ratio", "none"]
Weighting = Literal["1", "1/x", "1/x^2", "1/y", "1/y^2"]
LogBase = Literal["e", "2", "10", "none"]
OutlierRule = Literal["none", "grubbs", "rosner", "iqr", "zscore"]


# ────────────────────── core blocks ──────────────────────
class CurveFit(BaseModel):
    model: CurveModel = "4PL"
    weighting: Weighting = "1"
    log_x: LogBase = "10"
    log_y: LogBase = "none"


class PotencyOptions(BaseModel):
    method: PotencyMethod = "none"
    reference_label: Optional[str] = None  # name of reference curve/sample
    max_slope_ratio: PositiveFloat = 1.20  # used only if method != 'none'
    ci_level: PositiveFloat = 0.95


class AnalyticalRange(BaseModel):
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


class DuplicateCriteria(BaseModel):
    max_cv_percent: PositiveFloat = 10.0


class ControlWindow(BaseModel):
    qc_id: str
    min_value: PositiveFloat
    max_value: PositiveFloat
    units: str = "ng/mL"


class SpikeRecovery(BaseModel):
    spike_id: str
    added_conc: PositiveFloat
    target_recovery_pct: tuple[PositiveFloat, PositiveFloat] = (80.0, 120.0)
    units: str = "ng/mL"


class LinearityRules(BaseModel):
    r_squared_min: PositiveFloat = 0.98
    per_level_acc_pct: PositiveFloat = 15.0
    min_levels_pass: PositiveFloat = 0.75  # fraction (0‑1)


class DilutionLinearity(BaseModel):
    max_bias_pct: PositiveFloat = 20.0
    max_cv_pct: PositiveFloat = 20.0
    min_levels: int = 3


class HookEffectCheck(BaseModel):
    threshold_pct_of_undiluted: PositiveFloat = 80.0


class TotalErrorRule(BaseModel):
    overall_pct: PositiveFloat = 30.0
    loq_pct: PositiveFloat = 40.0


class RobustnessFactor(BaseModel):
    name: str  # e.g. "Incubation Temp"
    low: str  # "20 °C"
    high: str  # "28 °C"
    acceptance: str | None = None


class RobustnessDoE(BaseModel):
    factors: List[RobustnessFactor] = []


class QCSpec(BaseModel):
    duplicate_cv: DuplicateCriteria = DuplicateCriteria()
    controls: List[ControlWindow] = []  # kit or in‑house QCs
    spikes: List[SpikeRecovery] = []
    standards_nominal: List[PositiveFloat] | None = None  # Std‑0 … Std‑N
    linearity: LinearityRules = LinearityRules()
    dilution: DilutionLinearity = DilutionLinearity()
    hook: HookEffectCheck = HookEffectCheck()
    total_error: TotalErrorRule = TotalErrorRule()
    robustness: RobustnessDoE = RobustnessDoE()
    analytical_range: AnalyticalRange | None = None


class OutlierParams(BaseModel):
    rule: OutlierRule = "none"
    z_threshold: PositiveFloat | None = 3.0
    grubbs_alpha: PositiveFloat = 0.05
    iqr_k: PositiveFloat = 1.5


class SampleProcessing(BaseModel):
    blank_subtract: bool = True
    normalize_to_control: Optional[str] = None
    outliers: OutlierParams = OutlierParams()


class CalibrationCurve(BaseModel):
    min_levels: int = 6
    allow_anchor: bool = True
    backcalc_acc_pct: PositiveFloat = 15.0  # ±25 % for LLOQ/ULOQ handled in code


class CarryoverCheck(BaseModel):
    blank_threshold_pct_lloq: PositiveFloat = 20.0


# ────────────────────── root schema ──────────────────────
class ElisaAnalysisConfig(BaseModel):
    curve_fit: CurveFit = CurveFit()
    potency: PotencyOptions = PotencyOptions()
    qc: QCSpec = QCSpec()
    sample: SampleProcessing = SampleProcessing()
    calibration: CalibrationCurve = CalibrationCurve()
    carryover: CarryoverCheck = CarryoverCheck()
