from __future__ import annotations
from enum import StrEnum


class CurveModel(StrEnum):
    FOUR_PL = "4PL"
    FIVE_PL = "5PL"
    LINEAR = "linear"


class PotencyMethod(StrEnum):
    PARALLEL_LINE = "parallel_line"
    EC50_RATIO = "ec50_ratio"


class Weighting(StrEnum):
    ONE = "1"
    ONE_OVER_X = "1/x"
    ONE_OVER_X2 = "1/x^2"
    ONE_OVER_Y = "1/y"
    ONE_OVER_Y2 = "1/y^2"


class LogBase(StrEnum):
    LN = "e"
    LOG2 = "2"
    LOG10 = "10"


class OutlierRule(StrEnum):
    GRUBBS = "grubbs"
    ROSNER = "rosner"
    IQR = "iqr"
    ZSCORE = "zscore"
