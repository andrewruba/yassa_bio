from __future__ import annotations

from pydantic import Field, PositiveFloat

from yassa_bio.core.model import SchemaModel
from yassa_bio.core.typing import Fraction01
from yassa_bio.schema.analysis.enum import OutlierRule
from yassa_bio.core.enum import enum_examples


class OutlierParams(SchemaModel):
    """
    Settings for detecting outliers among replicate wells.
    """

    rule: OutlierRule = Field(
        OutlierRule.NONE,
        description=(
            "Statistical test to apply for outlier detection "
            "(e.g., Grubbs, Rosner, IQR)."
        ),
        examples=enum_examples(OutlierRule),
    )
    z_threshold: PositiveFloat = Field(
        3.0,
        ge=2,
        le=10,
        description=(
            "Z-score threshold for identifying outliers (used if rule is zscore)."
        ),
    )
    grubbs_alpha: PositiveFloat = Fraction01(
        0.05, description="Significance level for Grubbs or Rosner outlier tests."
    )
    iqr_k: PositiveFloat = Field(
        1.5,
        gt=0,
        le=5,
        description=(
            "Multiplier for IQR method; defines cutoff from the interquartile range."
        ),
    )


class Preprocessing(SchemaModel):
    """
    Preprocessing rules applied to sample measurements.
    """

    blank_subtract: bool = Field(
        True,
        description="If True, subtract blank well signal from all sample measurements.",
    )
    normalize_to_control: bool = Field(
        False,
        description=(
            "If True, normalize each sample signal to the calibration standard range."
        ),
    )
    outliers: OutlierParams = OutlierParams()
