from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)

from yassa_bio.core.typing import Percent


class AccuracySpec(BaseModel):
    """
    Acceptance criteria to determine the closeness of measured value to true value.
    """

    min_levels: int = Field(
        5,
        ge=3,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    min_replicates_per_level: int = Field(
        3,
        ge=1,
        description=(
            "Minimum replicate wells analysed at each calibration standard level."
        ),
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) at LOW, MID, HIGH levels.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    total_error_pct_mid: PositiveFloat = Percent(
        30,
        description="Total-error limit (%) at LOW, MID, HIGH levels.",
    )
    total_error_pct_edge: PositiveFloat = Percent(
        40,
        description="Total-error limit (%) at LLOQ and ULOQ.",
    )
