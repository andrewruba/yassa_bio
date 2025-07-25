from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


class AnalyticalParallelismSpec(BaseModel):
    """
    Acceptance criteria for detecting non–parallel behaviour between
    the calibration curve and serially-diluted study samples.
    """

    # sample_id not a field anymore in well
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
        ge=0,
        description="Minimum distinct dilution factors that must be tested.",
    )
    min_replicates: int = Field(
        3,
        ge=1,
        description=(
            "Minimum number of replicate wells required for each dilution factor."
        ),
    )

    cv_tol_pct: PositiveFloat = Percent(
        30,
        description=(
            "Maximum allowed %CV among back-calculated concentrations "
            "after adjusting for dilution."
        ),
    )
