from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


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

    blank_thresh_pct_lloq: PositiveFloat = Percent(
        20, description="Blank signal must be < this % of LLOQ response."
    )
