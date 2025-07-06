from __future__ import annotations
from enum import StrEnum


class CurveModel(StrEnum):
    FOUR_PL = "4PL"
    FIVE_PL = "5PL"
    LINEAR = "linear"


class Weighting(StrEnum):
    ONE = "1"
    ONE_OVER_X = "1/x"
    ONE_OVER_X2 = "1/x^2"
    ONE_OVER_Y = "1/y"
    ONE_OVER_Y2 = "1/y^2"


class Transformation(StrEnum):
    IDENTITY = "identity"
    LN = "ln"
    LOG2 = "log2"
    LOG10 = "log10"
    SQRT = "sqrt"
    RECIPROCAL = "reciprocal"


class OutlierRule(StrEnum):
    NONE = "none"
    GRUBBS = "grubbs"
    ROSNER = "rosner"
    IQR = "iqr"
    ZSCORE = "zscore"


class BlankRule(StrEnum):
    NONE = "none"
    MEAN = "mean"
    MEDIAN = "median"
    MINIMUM = "min"


class NormRule(StrEnum):
    NONE = "none"
    SPAN = "span"
    MAX = "max"
