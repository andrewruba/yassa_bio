from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


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
