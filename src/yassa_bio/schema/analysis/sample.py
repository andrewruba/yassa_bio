from __future__ import annotations
from typing import Optional
from pydantic import PositiveFloat

from yassa_bio.core.model import StrictModel
from yassa_bio.schema.analysis.enum import OutlierRule


class OutlierParams(StrictModel):
    rule: Optional[OutlierRule] = None
    z_threshold: PositiveFloat | None = 3.0
    grubbs_alpha: PositiveFloat = 0.05
    iqr_k: PositiveFloat = 1.5


class SampleProcessing(StrictModel):
    blank_subtract: bool = True
    normalize_to_control: Optional[str] = None
    outliers: OutlierParams = OutlierParams()
