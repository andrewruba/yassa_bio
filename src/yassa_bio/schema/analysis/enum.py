from __future__ import annotations
from typing import Literal

CurveModel = Literal["4PL", "5PL", "linear"]
PotencyMethod = Literal["parallel_line", "ec50_ratio"]
Weighting = Literal["1", "1/x", "1/x^2", "1/y", "1/y^2"]
LogBase = Literal["e", "2", "10"]
OutlierRule = Literal["grubbs", "rosner", "iqr", "zscore"]
