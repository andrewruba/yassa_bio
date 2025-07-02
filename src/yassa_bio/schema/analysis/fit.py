from __future__ import annotations
from typing import Optional
from pydantic import (
    Field,
    PositiveFloat,
    model_validator,
)

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.enum import (
    CurveModel,
    Weighting,
    LogBase,
    PotencyMethod,
)
from yassa_bio.core.typing import Fraction01


class CurveFit(SchemaModel):
    """
    Parameters defining the mathematical model used for fitting the calibration curve.
    """

    model: CurveModel = Field(
        CurveModel.FOUR_PL,
        description="Mathematical model used to fit the standard curve (e.g., 4PL, 5PL, or linear).",
    )
    weighting: Optional[Weighting] = Field(
        None,
        description="Optional weighting scheme applied to curve fit residuals (e.g., 1/y).",
    )
    log_x: Optional[LogBase] = Field(
        None, description="Log transformation applied to x-values prior to fitting."
    )
    log_y: Optional[LogBase] = Field(
        None,
        description="Log transformation applied to y-values prior to fitting.",
    )


class PotencyOptions(SchemaModel):
    """
    Configuration for relative potency estimation.
    """

    method: Optional[PotencyMethod] = Field(
        None,
        description="Approach to compute relative potency (e.g., parallel-line or EC50 ratio).",
    )
    min_slope_ratio: PositiveFloat = Field(
        0.80,
        description="Minimum allowable ratio between slopes in parallel-line analysis.",
    )
    max_slope_ratio: PositiveFloat = Field(
        1.20,
        description="Maximum allowable ratio between slopes in parallel-line analysis.",
    )
    ci_level: PositiveFloat = Fraction01(
        0.95, description="Confidence level for potency estimate (e.g., 0.95 = 95%)."
    )

    @model_validator(mode="after")
    def _check_method_vs_curve(self):
        curve_model: CurveModel = self.__pydantic_extra__["_curve_model"]
        if self.method is None:
            self.method = (
                PotencyMethod.PARALLEL_LINE
                if curve_model is CurveModel.LINEAR
                else PotencyMethod.EC50_RATIO
            )
        if (
            self.method == PotencyMethod.PARALLEL_LINE
            and curve_model != CurveModel.LINEAR
        ):
            raise ValueError(
                "parallel_line potency requires curve_fit.model == 'linear'"
            )
        if self.method == PotencyMethod.EC50_RATIO and curve_model == CurveModel.LINEAR:
            raise ValueError("ec50_ratio potency requires a non-linear curve model")
        return self
