from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List, Optional

from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage
from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.layout.well import Well


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    qc_level: Optional[QCLevel] = None
    needs_interferent: bool = False
    carryover: bool = False
    needs_stability_condition: bool = False
    needs_sample_id: bool = False
    recovery_stage: Optional[RecoveryStage] = None

    def matches(self, well: Well) -> bool:
        if well.sample_type != self.sample_type:
            return False

        if self.qc_level is not None and well.qc_level != self.qc_level:
            return False

        if self.needs_interferent != (well.interferent is not None):
            return False

        if well.carryover != self.carryover:
            return False

        if self.needs_stability_condition != (well.stability_condition is not None):
            return False

        if self.recovery_stage is not None and (
            well.recovery_stage != self.recovery_stage
        ):
            return False

        return True


class SpecificitySpec(BaseModel):
    """
    Acceptance criteria to ensure binding reagent binds to target analyte and
    doesn't cross-react with structurally related, interferent molecules.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.BLANK,
                needs_interferent=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LLOQ,
                needs_interferent=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.ULOQ,
                needs_interferent=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    bias_tol_pct: PositiveFloat = Percent(
        25, description="Maximum allowed bias (±) at LLOQ & ULOQ with interferent."
    )
    blank_thresh_pct_lloq: PositiveFloat = Percent(
        20, description="Blank + interferent must be < this % of LLOQ response."
    )


class SelectivitySpec(BaseModel):
    """
    Acceptance criteria to ensure the detection and differentiation of the
    analyte of interest in the presence of non-specific matrix components.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(sample_type=SampleType.BLANK),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LLOQ
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.HIGH
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_sources: int = Field(
        10, ge=1, description="Minimum number of individual blank matrices."
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.80, description="Fraction of sources that must meet each criterion."
    )

    blank_thresh_pct_lloq: PositiveFloat = Percent(
        20, description="Blank signal must be < this % of LLOQ response."
    )
    acc_tol_pct_lloq: PositiveFloat = Percent(
        25, description="Allowed bias for LLOQ-spiked QC."
    )
    acc_tol_pct_high: PositiveFloat = Percent(
        20, description="Allowed bias for High-QC-spiked QC."
    )


class CalibrationSpec(BaseModel):
    """
    Acceptance criteria that demonstrates the relationship between the
    nominal analyte concentration and the response of the
    analytical platform to the analyte.
    """

    min_levels: int = Field(
        6,
        ge=3,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.75,
        description=(
            "Fraction of calibration levels that must meet accuracy / precision "
            "criteria."
        ),
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) for NON-edge standards.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    prec_cv_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Precision CV tolerance (%) for NON-edge standards.",
    )
    prec_cv_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Precision CV tolerance (%) at LLOQ and ULOQ.",
    )


class AccuracySpec(BaseModel):
    """
    Acceptance criteria to determine the closeness of measured value to true value.
    """

    min_levels: int = Field(
        5,
        ge=3,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    min_replicates_per_level: int = Field(
        3,
        ge=1,
        description=(
            "Minimum replicate wells analysed at each calibration standard level."
        ),
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) at LOW, MID, HIGH levels.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    total_error_pct_mid: PositiveFloat = Percent(
        30,
        description="Total-error limit (%) at LOW, MID, HIGH levels.",
    )
    total_error_pct_edge: PositiveFloat = Percent(
        40,
        description="Total-error limit (%) at LLOQ and ULOQ.",
    )


class PrecisionSpec(BaseModel):
    """
    Acceptance criteria to determine the scatter in repeat measurements.
    """

    min_levels: int = Field(
        5,
        ge=3,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    min_replicates_per_level: int = Field(
        3,
        ge=1,
        description=(
            "Minimum replicate wells analysed at each calibration standard level."
        ),
    )

    cv_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Precision CV limit (%) for LOW, MID, HIGH levels.",
    )
    cv_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Precision CV limit (%) at LLOQ and ULOQ.",
    )
    total_error_pct_mid: PositiveFloat = Percent(
        30,
        description="Total-error limit (%) for LOW, MID, HIGH levels.",
    )
    total_error_pct_edge: PositiveFloat = Percent(
        40,
        description="Total-error limit (%) at LLOQ and ULOQ.",
    )


class CarryoverSpec(BaseModel):
    """
    Acceptance criteria to determine if there is residual analyte from
    a high sample affecting the next sample.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.BLANK,
                carryover=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_blanks_after_uloq: int = Field(
        0,
        ge=0,
        description=(
            "Number of blank wells that must be placed immediately after the ULOQ."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        1.0,
        description=(
            "Fraction of those blanks that must meet the threshold. "
            "Keep at 1.0 to require every blank to pass."
        ),
    )

    blank_thresh_pct_lloq: PositiveFloat = Percent(
        20, description="Blank signal must be < this % of LLOQ response."
    )


class DilutionLinearitySpec(BaseModel):
    """
    Acceptance criteria for validating accuracy when diluting samples
    from above the calibration range.
    """

    min_dilution_factors: int = Field(
        3,
        ge=0,
        description="Distinct dilution factors that must be tested.",
    )
    min_series: int = Field(
        3,
        ge=1,
        description=(
            "Independently prepared dilution series required for each factor."
        ),
    )
    min_replicates_per_point: int = Field(
        3,
        ge=1,
        description="Replicate wells analysed per dilution point.",
    )
    pass_fraction: PositiveFloat = Fraction01(
        1.0,
        description=(
            "Fraction of dilution points (series × factor) that must meet limits. "
            "1.0 = every point must pass."
        ),
    )

    bias_tol_pct: PositiveFloat = Percent(
        20,
        description="Maximum bias (%) after correcting for the dilution factor.",
    )
    cv_tol_pct: PositiveFloat = Percent(
        20,
        description="Maximum precision CV (%) across replicates at each dilution.",
    )

    hook_check_threshold_pct: PositiveFloat = Percent(
        80,
        description=(
            "Undiluted sample (above ULOQ) must recover ≥ this % of its own "
            "diluted concentrations (guards against hook effect)."
        ),
    )


class StabilitySpec(BaseModel):
    """
    Acceptance criteria to determine that every step taken during
    sample preparation, processing and analysis as well as the
    storage conditions used do not affect the concentration of the analyte.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                needs_stability_condition=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                needs_stability_condition=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_conditions: int = Field(
        0,
        ge=0,
        description="Total distinct stability conditions that must be evaluated.",
    )
    pass_fraction: PositiveFloat = Fraction01(
        1.0,
        description="Fraction of QC aliquots that must meet limits in each condition.",
    )

    bias_tol_pct: PositiveFloat = Percent(
        20,
        description="Mean bias (± %) allowed at each QC level.",
    )


class ParallelismSpec(BaseModel):
    """
    Acceptance criteria for detecting non–parallel behaviour between
    the calibration curve and serially-diluted study samples.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.SAMPLE,
                needs_sample_id=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_dilutions: int = Field(
        3,
        ge=1,
        description="Minimum number of distinct dilution factors to test.",
    )
    min_replicates_each: int = Field(
        3,
        ge=1,
        description="Replicate wells for each point in every dilution series.",
    )

    cv_tol_pct: PositiveFloat = Percent(
        30,
        description=(
            "Maximum allowed %CV among back-calculated concentrations "
            "within a dilution series."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        1.0,
        description="Fraction of dilution series that must meet the %CV limit.",
    )


class RecoverySpec(BaseModel):
    """
    Acceptance criteria for extraction recovery (efficiency and consistency).
    """

    required_well_patterns: list[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.MID,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                recovery_stage=RecoveryStage.AFTER,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.MID,
                recovery_stage=RecoveryStage.AFTER,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                recovery_stage=RecoveryStage.AFTER,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_replicates_each: int = Field(
        3,
        ge=1,
        description="Replicate wells for each (stage × QC level) combination.",
    )

    max_cv_pct_within_level: PositiveFloat = Percent(
        15,
        description="CV (%) of recovery at each QC level.",
    )
    max_diff_pct_between_levels: PositiveFloat = Percent(
        15,
        description=("Absolute % difference between mean recoveries at each QC level."),
    )


class LBAValidationAcceptanceCriteria(BaseModel):
    specificity: SpecificitySpec = SpecificitySpec()
    selectivity: SelectivitySpec = SelectivitySpec()
    calibration: CalibrationSpec = CalibrationSpec()
    accuracy: AccuracySpec = AccuracySpec()
    precision: PrecisionSpec = PrecisionSpec()
    carryover: CarryoverSpec = CarryoverSpec()
    dilution_linearity: DilutionLinearitySpec = DilutionLinearitySpec()
    stability: StabilitySpec = StabilitySpec()
    parallelism: ParallelismSpec = ParallelismSpec()
    recovery: RecoverySpec = RecoverySpec()


# TODO:
# 2) structure spec logic
#   - search "Yes —formalizing the common skeleton pays off"
