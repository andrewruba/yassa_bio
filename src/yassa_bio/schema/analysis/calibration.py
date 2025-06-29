from __future__ import annotations
from pydantic import PositiveFloat, Field

from yassa_bio.core.model import SchemaModel
from yassa_bio.core.typing import Percent


class CalibrationCurve(SchemaModel):
    min_levels: int = Field(6, ge=2)
    allow_anchor: bool = True
    backcalc_acc_pct: PositiveFloat = Percent(15.0, description="±% for interior stds")
    edge_acc_pct: PositiveFloat = Percent(25.0, description="±% for LLOQ/ULOQ")


class CarryoverCheck(SchemaModel):
    blank_threshold_pct_lloq: PositiveFloat = Percent(20.0)
    analyte_pct_of_lloq: PositiveFloat = Percent(20.0)
    internal_std_pct_of_ref: PositiveFloat = Percent(5.0)
