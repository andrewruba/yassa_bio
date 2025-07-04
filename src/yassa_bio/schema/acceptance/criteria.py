from pydantic import (
    BaseModel,
    Field,
    NonNegativeFloat,
)
from typing import List, Optional

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent
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
    bias_tol_pct: NonNegativeFloat = Percent(
        25, description="Maximum allowed bias (±) at LLOQ & ULOQ with interferent."
    )
    blank_thresh_pct_lloq: NonNegativeFloat = Percent(
        100, description="Blank + interferent must be < this % of LLOQ response."
    )


# class SelectivitySpec(BaseModel):
#     n_matrices: int = Field(10, ge=6)
#     blank_below_lloq_threshold: Percent = 100  # % of LLOQ (i.e. < LLOQ)
#     min_pass_rate: Percent = Field(80, description="≥80 % of matrices pass")
#     acc_tolerance_lloq: Percent = 25
#     acc_tolerance_hqc: Percent = 20


# class CalibrationSpec(BaseModel):
#     min_levels: int = 6
#     fit_model_allowed: List[str] = ["4PL", "5PL"]
#     anchor_allowed: bool = True
#     acc_pct_core: Percent = 20
#     acc_pct_edges: Percent = 25
#     min_levels_pass_pct: Percent = 75


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
