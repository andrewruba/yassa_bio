from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List, Optional

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.layout.well import Well


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    needs_interferent: bool = True
    qc_level: Optional[QCLevel] = None

    def matches(self, well: Well) -> bool:
        if well.sample_type != self.sample_type:
            return False
        if self.qc_level is not None and well.qc_level != self.qc_level:
            return False
        if self.needs_interferent and well.interferent is None:
            return False
        if not self.needs_interferent and well.interferent is not None:
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
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LLOQ,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.ULOQ,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    bias_tol_pct: PositiveFloat = Percent(
        25, description="Maximum allowed bias (±) at LLOQ & ULOQ with interferent."
    )
    blank_thresh_pct_lloq: PositiveFloat = Percent(
        100, description="Blank + interferent must be < this % of LLOQ response."
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
        100, description="Blank signal must be < this % of LLOQ response."
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
            "Minimum number of *calibration* levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.75,
        description=(
            "Fraction of calibration levels that must meet accuracy / precision "
            "criteria (≥ 75 %)."
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


# class AccuracySpec(BaseModel):
#     core_bias_pct: Percent = Field(20, description="±20 % bias, mid-range QCs")
#     edge_bias_pct: Percent = Field(25, description="±25 % bias at LLOQ / ULOQ")
#     total_error_core: Percent = 30  # |bias| + CV
#     total_error_edges: Percent = 40
#     n_qc_levels: int = 5  # LLOQ, low, mid, high, ULOQ
#     reps_per_run: int = 3
#     runs_required: int = 6


# class PrecisionSpec(BaseModel):
#     core_cv_pct: Percent = Field(20, description="≤20 % CV, mid-range QCs")
#     edge_cv_pct: Percent = Field(25, description="≤25 % CV at LLOQ / ULOQ")
#     total_error_core: Percent = 30
#     total_error_edges: Percent = 40
#     reps_per_run: int = 3
#     runs_required: int = 6


# class CarryoverSpec(BaseModel):
#     blank_pct_of_lloq: Percent = 100  # < LLOQ
#     internal_std_pct_ref: Percent = 5  # optional; set None for LBA


# class DilutionLinearitySpec(BaseModel):
#     bias_pct: Percent = 20
#     cv_pct: Percent = 20
#     min_dil_levels: int = 3
#     min_series: int = 3
#     hook_threshold_pct: Percent = 80  # undiluted ≥80 % of diluted


# class StabilitySpec(BaseModel):
#     qc_tolerance_pct: Percent = 20
#     conditions_required: List[str] = [
#         "autosampler",
#         "bench_top",
#         "extracted",
#         "freeze_thaw",
#         "long_term",
#         "stock_solution",
#     ]
#     freeze_thaw_cycles: int = 3


# class ParallelismSpec(BaseModel):
#     max_cv_pct: Percent = 30
#     min_dilutions: int = 3


# # ── Top-level acceptance container ────────────────────────────────────────────
# class LBAAcceptanceCriteria(BaseModel):
#     specificity: SpecificitySpec = SpecificitySpec()
#     selectivity: SelectivitySpec = SelectivitySpec()
#     calibration: CalibrationSpec = CalibrationSpec()
#     accuracy: AccuracySpec = AccuracySpec()
#     precision: PrecisionSpec = PrecisionSpec()
#     carryover: CarryoverSpec = CarryoverSpec()
#     dilution_linearity: DilutionLinearitySpec = DilutionLinearitySpec()
#     stability: StabilitySpec = StabilitySpec()
#     parallelism: ParallelismSpec = ParallelismSpec()
