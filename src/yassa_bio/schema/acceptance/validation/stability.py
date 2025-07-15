from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


class StabilitySpec(BaseModel):
    """
    Acceptance criteria to determine that every step taken during
    sample preparation, processing and analysis as well as the
    storage conditions used do not affect the concentration of the analyte.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                needs_stability_condition=True,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                needs_stability_condition=True,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_conditions: int = Field(
        0,
        ge=0,
        description="Total distinct stability conditions that must be evaluated.",
    )

    acc_tol_pct: PositiveFloat = Percent(
        20,
        description="Mean accuracy tolerance (± %) allowed at each QC level.",
    )
