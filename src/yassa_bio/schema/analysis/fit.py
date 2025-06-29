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
    weighting: Weighting = "1"
    log_x: LogBase = "10"
    log_y: LogBase = "none"


class PotencyOptions(StrictModel):
    method: PotencyMethod = "none"
    reference_label: Optional[str] = None  # name of reference curve/sample
    max_slope_ratio: PositiveFloat = 1.20  # used only if method != 'none'
    ci_level: PositiveFloat = 0.95
