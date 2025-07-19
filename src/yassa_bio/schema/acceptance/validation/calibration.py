from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)
from typing import List

from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


class CalibrationSpec(BaseModel):
    """
    Acceptance criteria that demonstrates the relationship between the
    nominal analyte concentration and the response of the
    analytical platform to the analyte.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.CALIBRATION_STANDARD,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_levels: int = Field(
        6,
        ge=2,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.75,
        description=(
            "Fraction of calibration levels that must meet accuracy / precision "
            "criteria."
        ),
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) for NON-edge standards.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    cv_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Precision CV tolerance (%) for NON-edge standards.",
    )
    cv_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Precision CV tolerance (%) at LLOQ and ULOQ.",
    )
