from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


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
