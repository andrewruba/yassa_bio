from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class PrecisionSpec(BaseModel):
    """
    Acceptance criteria to determine the scatter in repeat measurements.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LLOQ
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.HIGH
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.ULOQ
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_levels: int = Field(
        5,
        ge=1,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    min_replicates_per_level: int = Field(
        3,
        ge=1,
        description=("Minimum replicate wells analysed at each quality control level."),
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
