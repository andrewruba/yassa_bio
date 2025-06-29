from __future__ import annotations
from typing import Optional
from pydantic import PositiveFloat, field_validator, model_validator, ValidationInfo

from yassa_bio.core.model import StrictModel
from yassa_bio.schema.analysis.enum import (
    CurveModel,
    Weighting,
    LogBase,
    PotencyMethod,
)


class CurveFit(StrictModel):
    model: CurveModel = "4PL"
    weighting: Optional[Weighting] = None
    log_x: Optional[LogBase] = None
    log_y: Optional[LogBase] = None

    @field_validator("weighting")
    def _weighting_vs_model(cls, v, info: ValidationInfo):
        if info.data.get("model") == "linear" and v is not None:
            raise ValueError("weighting has no effect when model == 'linear'")
        return v

    @model_validator(mode="after")
    def _log_rules(self):
        if self.model == "linear":
            if self.log_y is not None:
                raise ValueError("log_y must be None for linear model")
        else:
            if self.log_x is None:
                raise ValueError("log_x is required for 4PL / 5PL fits")
        return self


class PotencyOptions(StrictModel):
    method: Optional[PotencyMethod] = None
    max_slope_ratio: PositiveFloat = 1.20
    ci_level: PositiveFloat = 0.95

    @model_validator(mode="after")
    def _check_method_vs_curve(self):
        curve_model: str = self.__pydantic_extra__["_curve_model"]
        if self.method is None:
            self.method = "parallel_line" if curve_model == "linear" else "ec50_ratio"
        if self.method == "parallel_line" and curve_model != "linear":
            raise ValueError(
                "parallel_line potency requires curve_fit.model == 'linear'"
            )
        if self.method == "ec50_ratio" and curve_model == "linear":
            raise ValueError("ec50_ratio potency requires a non-linear curve model")
        return self
