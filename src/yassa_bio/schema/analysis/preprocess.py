from __future__ import annotations

from pydantic import Field, PositiveFloat

from yassa_bio.core.model import SchemaModel
from yassa_bio.core.typing import Fraction01
from yassa_bio.schema.analysis.enum import OutlierRule, BlankRule, NormRule
from yassa_bio.core.enum import enum_examples


class OutlierParams(SchemaModel):
    """
    Settings for detecting outliers among replicate wells.
    """

    rule: OutlierRule = Field(
        OutlierRule.NONE,
        description=(
            "Statistical test to apply for outlier detection "
            "(e.g., Grubbs, Z-score, IQR)."
        ),
        examples=enum_examples(OutlierRule),
    )
    z_threshold: PositiveFloat = Field(
        3.0,
        ge=0,
        description=(
            "Z-score threshold for identifying outliers (used if rule is zscore)."
        ),
    )
    grubbs_alpha: PositiveFloat = Fraction01(
        0.05, description="Significance level for Grubbs outlier test."
    )
    iqr_k: PositiveFloat = Field(
        1.5,
        gt=0,
        description=(
            "Multiplier for IQR method; defines cutoff from the interquartile range."
        ),
    )


class Preprocess(SchemaModel):
    """
    Preprocess rules applied to sample measurements.
    """

    blank_rule: BlankRule = Field(
        BlankRule.MEAN,
        description="Subtract blank well signal from all sample measurements.",
        examples=enum_examples(BlankRule),
    )
    norm_rule: NormRule = Field(
        NormRule.NONE,
        description="Normalize each sample signal to the calibration standard range.",
        examples=enum_examples(NormRule),
    )
    outliers: OutlierParams = OutlierParams()
