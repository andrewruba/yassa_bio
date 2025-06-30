from __future__ import annotations
from pydantic import PositiveFloat, Field

from yassa_bio.core.model import SchemaModel
from yassa_bio.core.typing import Percent


class CalibrationCurve(SchemaModel):
    min_levels: int = Field(
        6, ge=2, description="Minimum number of standards required to define the curve."
    )
    allow_anchor: bool = Field(
        True,
        description="Allow use of an additional anchor point to improve curve fitting at the low and high end.",
    )
    backcalc_acc_pct: PositiveFloat = Percent(
        15.0,
        description="Accuracy tolerance (%) for standards during back-calculation.",
    )
    edge_acc_pct: PositiveFloat = Percent(
        25.0, description="Accuracy tolerance (%) for LLOQ and ULOQ standards."
    )


class CarryoverCheck(SchemaModel):
    blank_threshold_pct_lloq: PositiveFloat = Percent(
        20.0, description="Maximum allowed blank signal as a percentage of LLOQ signal."
    )
    analyte_pct_of_lloq: PositiveFloat = Percent(
        20.0,
        description="Max analyte signal allowed in blanks following the highest standard (% of LLOQ).",
    )
    internal_std_pct_of_ref: PositiveFloat = Percent(
        5.0,
        description="Max internal standard signal allowed in blanks (% of reference IS signal).",
    )
