from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)

from yassa_bio.core.typing import Percent, Fraction01


class DilutionLinearitySpec(BaseModel):
    """
    Acceptance criteria for validating accuracy when diluting samples
    from above the calibration range.
    """

    min_dilution_factors: int = Field(
        3,
        ge=0,
        description="Distinct dilution factors that must be tested.",
    )
    min_series: int = Field(
        3,
        ge=1,
        description=(
            "Independently prepared dilution series required for each factor."
        ),
    )
    min_replicates_per_point: int = Field(
        3,
        ge=1,
        description="Replicate wells analysed per dilution point.",
    )
    pass_fraction: PositiveFloat = Fraction01(
        1.0,
        description=(
            "Fraction of dilution points (series × factor) that must meet limits. "
            "1.0 = every point must pass."
        ),
    )

    bias_tol_pct: PositiveFloat = Percent(
        20,
        description="Maximum bias (%) after correcting for the dilution factor.",
    )
    cv_tol_pct: PositiveFloat = Percent(
        20,
        description="Maximum precision CV (%) across replicates at each dilution.",
    )

    hook_check_threshold_pct: PositiveFloat = Percent(
        80,
        description=(
            "Undiluted sample (above ULOQ) must recover ≥ this % of its own "
            "diluted concentrations (guards against hook effect)."
        ),
    )
