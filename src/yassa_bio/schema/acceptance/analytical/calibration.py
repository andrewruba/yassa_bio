from pydantic import BaseModel, Field, PositiveFloat

from yassa_bio.core.typing import Percent, Fraction01


class AnalyticalCalibrationSpec(BaseModel):
    """
    Acceptance criteria for back-calculated concentrations of calibration standards
    in an analytical run.
    """

    min_levels: int = Field(
        6,
        ge=6,
        description=(
            "Minimum number of calibration levels (LLOQ, ULOQ included). "
            "Blank and anchor levels are not counted."
        ),
    )
    pass_fraction: PositiveFloat = Fraction01(
        0.75,
        description="Fraction of calibration levels that must pass.",
    )

    acc_tol_pct_mid: PositiveFloat = Percent(
        20,
        description="Accuracy tolerance (± %) for NON-edge standards.",
    )
    acc_tol_pct_edge: PositiveFloat = Percent(
        25,
        description="Accuracy tolerance (± %) at LLOQ and ULOQ.",
    )
    min_retained_levels: int = Field(
        6,
        ge=3,
        description=(
            "Minimum number of levels that may be retained after discarding and re-fit."
        ),
    )
