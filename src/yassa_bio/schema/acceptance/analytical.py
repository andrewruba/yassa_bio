from pydantic import BaseModel, Field, PositiveFloat
from typing import List

from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.validation import RequiredWellPattern


class AnalyticalCalibrationSpec(BaseModel):
    """
    Acceptance criteria for back-calculated concentrations of calibration standards
    in an analytical run.
    """

    min_levels: int = Field(
        6,
        ge=6,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.75,
        description="Fraction of calibration levels that must pass.",
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) for NON-edge standards.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    min_retained_levels: int = Field(
        6,
        ge=3,
        description=(
            "Minimum number of  levels that may be retained after "
            "discarding and re-fit."
        ),
    )


class AnalyticalQCSpec(BaseModel):
    """
    Acceptance criteria for accuracy/precision on QC samples in an analytical run.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.HIGH
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    qc_tol_pct: PositiveFloat = Percent(
        20, description="Per-well accuracy tolerance (± %)."
    )
    pass_fraction_total: PositiveFloat = Fraction01(
        2 / 3,
        description="Fractin of QC wells that must pass accuracy.",
    )
    pass_fraction_each_level: PositiveFloat = Fraction01(
        0.50,
        description="Fraction of wells at every QC level must pass.",
    )


class LBAAnalyticalAcceptanceCriteria(BaseModel):
    """
    Acceptance criteria for routine study-sample runs.
    """

    calibration: AnalyticalCalibrationSpec = AnalyticalCalibrationSpec()
    qc: AnalyticalQCSpec = AnalyticalQCSpec()
