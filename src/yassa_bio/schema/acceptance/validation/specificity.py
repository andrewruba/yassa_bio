from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


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

    acc_tol_pct: PositiveFloat = Percent(
        25, description="Accuracy tolerance (±) at LLOQ & ULOQ with interferent."
    )
    blank_thresh_pct_lloq: PositiveFloat = Percent(
        20, description="Blank + interferent must be < this % of LLOQ response."
    )
