from __future__ import annotations
from typing import Optional
from pydantic import Field, PositiveFloat, model_validator

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.enum import OutlierRule
from yassa_bio.core.typing import Fraction01


class OutlierParams(SchemaModel):
    rule: Optional[OutlierRule] = Field(
        None,
        description="Statistical test to apply for outlier detection (e.g., Grubbs, Rosner, IQR).",
    )
    z_threshold: PositiveFloat | None = Field(
        3.0,
        ge=2,
        le=10,
        description="Z-score threshold for identifying outliers (used if rule is zscore).",
    )
    grubbs_alpha: PositiveFloat = Fraction01(
        0.05, description="Significance level (α) for Grubbs or Rosner outlier tests."
    )
    iqr_k: PositiveFloat = Field(
        1.5,
        gt=0,
        le=5,
        description="Multiplier for IQR method; defines cutoff from the interquartile range.",
    )

    @model_validator(mode="after")
    def _rule_specific_params(self):
        if self.rule is None:
            return self
        if self.rule == OutlierRule.ZSCORE and self.z_threshold is None:
            raise ValueError("z_threshold required for zscore rule")
        if self.rule in {OutlierRule.GRUBBS, OutlierRule.ROSNER} and not (
            0 < self.grubbs_alpha < 1
        ):
            raise ValueError("grubbs_alpha must be in (0,1)")
        if self.rule == OutlierRule.IQR and self.iqr_k <= 0:
            raise ValueError("iqr_k must be > 0")
        return self


class SampleProcessing(SchemaModel):
    blank_subtract: bool = Field(
        True,
        description="If True, subtract blank well signal from all sample measurements.",
    )
    normalize_to_control: bool = Field(
        False,
        description=(
            "If True, normalize each sample signal to the control range. "
            "Requires HIGH and LOW control wells to be defined."
        ),
    )
    outliers: OutlierParams = Field(
        default_factory=OutlierParams,
        description="Outlier detection parameters applied to sample replicates.",
    )
