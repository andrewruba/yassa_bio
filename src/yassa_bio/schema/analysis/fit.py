from __future__ import annotations
from typing import Optional
from pydantic import PositiveFloat

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


class PotencyOptions(StrictModel):
    method: Optional[PotencyMethod] = None
    max_slope_ratio: PositiveFloat = 1.20  # used only if method != 'none'
    ci_level: PositiveFloat = 0.95
