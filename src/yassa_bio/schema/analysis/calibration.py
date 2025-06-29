from __future__ import annotations
from pydantic import PositiveFloat

from yassa_bio.core.model import SchemaModel


class CalibrationCurve(SchemaModel):
    min_levels: int = 6
    allow_anchor: bool = True
    backcalc_acc_pct: PositiveFloat = 15.0
    edge_acc_pct: PositiveFloat = 25.0


class CarryoverCheck(SchemaModel):
    blank_threshold_pct_lloq: PositiveFloat = 20.0
