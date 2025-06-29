from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    NonNegativeInt,
    model_validator,
)

# ────────────────────── enums ──────────────────────
AssayFormat = Literal[
    "sandwich", "competitive", "indirect", "bridging", "plaque_reduction", "cell_based"
]
ReadoutType = Literal["absorbance", "fluorescence", "luminescence", "electrochem"]
CurveModel = Literal["4PL", "5PL", "linear"]
PotencyMethod = Literal["parallel_line", "ec50_ratio", "none"]
Weighting = Literal["1", "1/x", "1/x^2", "1/y", "1/y^2"]
LogBase = Literal["e", "2", "10", "none"]
PlotType = Literal["curve", "residuals", "qq", "leverage"]
OutlierRule = Literal[
    "none",  # ← keep explicit “off”
    "grubbs",  # single-point Grubbs test
    "rosner",  # Rosner’s generalised ESD
    "iqr",  # Tukey IQR rule
    "zscore",  # |z| > k (threshold in cfg)
]


# ────────────────────── core blocks ──────────────────────
class Metadata(BaseModel):
    assay_name: str
    assay_format: AssayFormat
    sop_version: Optional[str] = None
    parsed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Timestamp when this config was generated.",
    )


class CurveFit(BaseModel):
    model: CurveModel = "4PL"
    weighting: Weighting = Field(
        "1", description="Residual weight; '1' means unweighted."
    )
    log_x: LogBase = Field(
        "10", description="Log transform for X axis; 'none' disables."
    )
    log_y: LogBase = Field(
        "none", description="Optional log transform for Y (signal) axis."
    )


class PotencyOptions(BaseModel):
    """
    How relative potency is derived once both curves are fitted.
    """

    method: PotencyMethod = Field(
        "none",
        description=(
            "'parallel_line' → classical slope–ratio analysis\n"
            "'ec50_ratio' → potency = C_ref / C_test (ratio of inflection points)\n"
            "'none' → no potency calculation"
        ),
    )
    ref_sample: Optional[str] = Field(
        None,
        description=(
            "Label or group name that should be treated as the Reference curve "
            "when computing potency. If None, the first plate-level reference is used."
        ),
    )


class AnalyticalLimits(BaseModel):
    """
    Global limits that decide whether a quantitative result is reportable.
    All values are in the same concentration units.
    """

    lod: PositiveFloat = Field(
        ...,
        description="Limit of Detection: smallest signal reliably distinguished from blank.",
    )
    loq: Optional[PositiveFloat] = Field(
        None,
        description="Limit of Quantitation: lowest concentration that can be quantified with acceptable precision/accuracy.",
    )
    lower_reportable: PositiveFloat = Field(
        ...,
        description="Lower end of the validated reportable range (results below are censored/flagged).",
    )
    upper_reportable: PositiveFloat = Field(
        ...,
        description="Upper end of the validated reportable range (results above are censored/flagged).",
    )
    units: str = Field(
        "ng/mL", description="Concentration units used for all limit values."
    )


class ControlRange(BaseModel):
    """
    Acceptance window for a kit-supplied QC control or in-house reference sample.
    A plate fails if the measured control falls outside [min_value, max_value].
    """

    qc_id: str = Field(
        ..., description="Identifier shown in the plate layout / SOP (e.g. 'QC-Low')."
    )
    min_value: PositiveFloat = Field(
        ...,
        description="Lower acceptance limit for the control’s concentration or activity.",
    )
    max_value: PositiveFloat = Field(
        ...,
        description="Upper acceptance limit for the control’s concentration or activity.",
    )
    units: str = Field("ng/mL", description="Units for min/max values.")


class DuplicateCriteria(BaseModel):
    """
    Requirements for agreement between replicate wells / samples.
    """

    max_cv_percent: PositiveFloat = Field(
        10.0, description="Allowed %CV among replicate wells."
    )


class StandardPanel(BaseModel):
    """
    The **expected** standard concentrations that must appear on each plate,
    listed in either ascending **or** descending order.
    """

    levels: List[PositiveFloat] = Field(
        ...,
        description="Nominal concentrations for Std-0, Std-1, … (order as prepared).",
    )
    units: str = Field("ng/mL", description="Concentration units for all levels.")
    allow_missing: bool = Field(
        False,
        description="If False, any missing standard well triggers a hard failure.",
    )


class SpikeLevel(BaseModel):
    """
    Configuration for a spike-recovery control.

    Each entry describes one set of spiked wells that are used to verify
    matrix effects / accuracy by comparing the recovered concentration to the
    amount intentionally added.
    """

    spike_id: str = Field(
        ...,
        description=(
            "Human-readable identifier for this spike group, e.g. "
            "'Spike-Low', 'Spike-Mid', or 'Spike-High'."
        ),
    )

    added_conc: PositiveFloat = Field(
        ...,
        description=(
            "Nominal concentration (same units as the assay) that was added to "
            "each sample in this spike group—for example 5.0 ng/mL."
        ),
    )

    min_recovery_pct: PositiveFloat = Field(
        80.0,
        description=("Lower acceptance limit for percent recovery."),
    )

    max_recovery_pct: PositiveFloat = Field(
        120.0,
        description=("Upper acceptance limit for percent recovery."),
    )

    units: str = Field(
        "ng/mL",
        description=("Concentration units for spiked samples."),
    )


class LinearityAcceptance(BaseModel):
    """Standard-curve linearity & back-calc accuracy rules (ICH M10 §4.2.3)."""

    r_squared_min: PositiveFloat = 0.98  # global curve fit
    per_level_acc_pct: PositiveFloat = 15.0  # ±15 % (±25 % for LLOQ/ULOQ)
    min_levels_pass: PositiveFloat = 0.75  # ≥75 % of levels must pass


class DilutionLinearitySpec(BaseModel):
    enabled: bool = False  # turn test on/off per study
    max_bias_pct: PositiveFloat = 20.0  # accuracy after dilution
    max_cv_pct: PositiveFloat = 20.0  # precision across dilutions
    min_levels: int = 3  # ≥3 dilution levels required


class HookEffectSpec(BaseModel):
    enabled: bool = False
    threshold_pct_of_undiluted: PositiveFloat = 80.0
    """If undiluted signal < this % of first dilution → flag hook effect."""


class TotalErrorSpec(BaseModel):
    """ICH M10 allows Total Error ≤30 % (≤40 % at LLOQ/ULOQ)."""

    enabled: bool = False
    limit_overall_pct: PositiveFloat = 30.0
    limit_loq_pct: PositiveFloat = 40.0


class RobustnessFactor(BaseModel):
    factor: str  # e.g. "Incubation Temp", "Wash Speed"
    low: str  # human-readable low setting (e.g. "20 °C")
    high: str  # high setting (e.g. "28 °C")
    acceptance: str | None = None
    """
    Optional free-text criterion (“<10 % shift vs nominal”).
    """


class RobustnessMatrix(BaseModel):
    """
    Design of Experiments (DoE) for robustness: each entry is a factor varied
    while others are nominal.  The pipeline can iterate & record pass/fail.
    """

    enabled: bool = False
    factors: List[RobustnessFactor] = []


class QCSpec(BaseModel):
    max_cv_percent: PositiveFloat = Field(
        20.0, description="Allowed %CV for replicate precision."
    )
    min_r_squared: PositiveFloat = Field(
        0.98, description="Minimum R² for standard-curve goodness-of-fit."
    )
    require_parallelism: bool = Field(
        False, description="Enable slope-parallelism test for potency assays."
    )
    max_slope_ratio: PositiveFloat = Field(
        1.20, description="Allowed test/STD slope ratio when parallelism required."
    )
    ci_level: PositiveFloat = Field(
        0.95, description="Confidence interval level for parallelism calculation."
    )
    duplicate: DuplicateCriteria = DuplicateCriteria()
    controls: List[ControlRange] = []  # arbitrary # of QC windows
    limits: Optional[AnalyticalLimits] = None  # LOD / LOQ / range
    standards: Optional[StandardPanel] = None  # expected std curve
    spikes: List[SpikeLevel] = []

    linearity: LinearityAcceptance = LinearityAcceptance()
    dilution_linearity: DilutionLinearitySpec = DilutionLinearitySpec()
    hook_effect: HookEffectSpec = HookEffectSpec()
    total_error: TotalErrorSpec = TotalErrorSpec()
    robustness: RobustnessMatrix = RobustnessMatrix()


class GrubbsParams(BaseModel):
    alpha: PositiveFloat = 0.05


class IQRParams(BaseModel):
    k: PositiveFloat = 1.5  # Tukey default


class SampleProcessing(BaseModel):
    blank_subtract: bool = Field(
        True, description="Subtract mean blank signal from all wells."
    )
    normalize_to_control: Optional[str] = Field(
        None, description="Control group name for 100 % reference."
    )
    outlier_rule: OutlierRule = Field(
        "none", description="Outlier test stated in the analysis SOP."
    )
    z_threshold: PositiveFloat | None = Field(
        3.0,
        description="Only used when outlier_rule=='zscore'.",
    )
    grubbs: GrubbsParams = Field(default_factory=GrubbsParams)
    iqr: IQRParams = Field(default_factory=IQRParams)


class ReportOptions(BaseModel):
    include_raw: bool = Field(True, description="Embed raw data table in report.")
    include_plots: bool = Field(True, description="Generate diagnostic plots.")
    plots: List[PlotType] = Field(
        default_factory=lambda: ["curve"], description="Plot types to include."
    )
    decimals: NonNegativeInt = Field(
        3, description="Decimal places for numeric results."
    )
    output_format: Literal["pdf", "html", "json"] = Field(
        "pdf", description="Primary output format."
    )

    @model_validator(mode="after")
    def _unique_plots(self):
        self.plots = list(dict.fromkeys(self.plots))
        return self


class Instrument(BaseModel):
    reader_model: Optional[str] = Field(
        None, description="Instrument model, e.g. 'Tecan Infinite 200 Pro'."
    )
    wavelength_nm: Optional[int] = Field(
        None, ge=200, le=900, description="Primary measurement wavelength (nm)."
    )
    readout: ReadoutType = Field(
        "absorbance", description="Detector type used for signal."
    )
    read_mode: Optional[str] = Field(
        None, description="Endpoint, kinetic, dual-λ, etc."
    )


class CalibrationSpec(BaseModel):
    min_levels: int = 6
    allow_anchor: bool = True
    backcalc_acc_pct: PositiveFloat = 15.0  # LLOQ/ULOQ default 25


class CarryoverSpec(BaseModel):
    required: bool = False
    blank_threshold_pct_lloq: PositiveFloat = 20.0


class ValidationDesign(BaseModel):
    runs: PositiveFloat = 6
    days: PositiveFloat = 2
    analysts: PositiveFloat = 2


# ────────────────────── root schema ──────────────────────
class ElisaAnalysisConfig(BaseModel):
    meta: Metadata
    curve_fit: CurveFit
    potency: PotencyOptions
    qc: QCSpec
    sample: SampleProcessing
    report: ReportOptions
    instrument: Optional[Instrument] = None
    calibration: CalibrationSpec = CalibrationSpec()
    carryover: CarryoverSpec = CarryoverSpec()
    validation_plan: Optional[ValidationDesign] = None

    model_config = dict(
        title="ElisaAnalysisConfig",
        extra="forbid",
        strict=True,
        frozen=True,
    )
