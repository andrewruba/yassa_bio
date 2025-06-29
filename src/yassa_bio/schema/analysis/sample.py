from __future__ import annotations
from typing import Optional
from pydantic import PositiveFloat, model_validator

from yassa_bio.core.model import StrictModel
from yassa_bio.schema.analysis.enum import OutlierRule


class OutlierParams(StrictModel):
    rule: Optional[OutlierRule] = None
    z_threshold: PositiveFloat | None = 3.0
    grubbs_alpha: PositiveFloat = 0.05
    iqr_k: PositiveFloat = 1.5

    @model_validator(mode="after")
    def _rule_specific_params(self):
        if self.rule is None:
            return self
        if self.rule == "zscore" and self.z_threshold is None:
            raise ValueError("z_threshold required for zscore rule")
        if self.rule in {"grubbs", "rosner"} and not (0 < self.grubbs_alpha < 1):
            raise ValueError("grubbs_alpha must be in (0,1)")
        if self.rule == "iqr" and self.iqr_k <= 0:
            raise ValueError("iqr_k must be > 0")
        return self


class SampleProcessing(StrictModel):
    blank_subtract: bool = True
    normalize_to_control: Optional[str] = None
    outliers: OutlierParams = OutlierParams()
