from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern


class ValidationSelectivitySpec(BaseModel):
    """
    Acceptance criteria to ensure the detection and differentiation of the
    analyte of interest in the presence of non-specific matrix components.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.BLANK,
                needs_matrix_type=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LLOQ,
                needs_matrix_type=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                needs_matrix_type=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_sources: int = Field(
        10,
        ge=1,
        description=(
            "Minimum number of individual matrix sources to evaluate for selectivity. "
            "Each source should contribute a blank sample and be spiked "
            "at LLOQ and high QC."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.80,
        description=(
            "Minimum fraction of matrix sources that must pass all selectivity checks."
        ),
    )

    acc_tol_pct_lloq: PositiveFloat = Percent(
        25, description="Accuracy tolerance (±) for LLOQ-spiked QC."
    )
    acc_tol_pct_high: PositiveFloat = Percent(
        20, description="Accuracy tolerance (±) High-QC-spiked QC."
    )
