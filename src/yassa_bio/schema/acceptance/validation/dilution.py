from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.core.typing import Percent
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern


class ValidationDilutionLinearitySpec(BaseModel):
    """
    Acceptance criteria for validating accuracy when diluting samples
    from above the calibration range.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.ABOVE_ULOQ,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_dilutions: int = Field(
        3,
        ge=0,
        description=(
            "Minimum distinct dilution factors that must be tested in the "
            "calibration range."
        ),
    )
    min_replicates: int = Field(
        3,
        ge=1,
        description=(
            "Minimum number of replicate wells required for each dilution factor."
        ),
    )

    acc_tol_pct: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (%) after correcting for the dilution factor.",
    )
    cv_tol_pct: PositiveFloat = Percent(
        20,
        description="Maximum precision CV (%) across replicates at each dilution.",
    )

    undiluted_recovery_min_pct: PositiveFloat = Percent(
        80,
        description=(
            "Undiluted sample (above ULOQ) must recover ≥ this % of its own "
            "diluted concentrations (guards against hook effect)."
        ),
    )
