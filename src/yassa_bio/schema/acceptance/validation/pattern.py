from pydantic import BaseModel
from typing import Optional
import pandas as pd

from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    qc_level: Optional[QCLevel] = None
    needs_interferent: bool = False
    carryover: bool = False
    needs_stability_condition: bool = False
    needs_sample_id: bool = False
    recovery_stage: Optional[RecoveryStage] = None

    def mask(self, df: pd.DataFrame) -> pd.Series:
        m = df["sample_type"] == self.sample_type.value

        if self.qc_level is not None:
            m &= df["qc_level"] == self.qc_level.value

        if self.needs_interferent:
            m &= df["interferent"].notna()

        if self.carryover:
            m &= df["carryover"]

        if self.needs_stability_condition:
            m &= df["stability_condition"].notna()

        if self.recovery_stage is not None:
            m &= df["recovery_stage"] == self.recovery_stage.value

        if self.needs_sample_id:
            m &= df["sample_id"].notna()

        return m

    def present(self, df: pd.DataFrame) -> bool:
        return self.mask(df).any()
