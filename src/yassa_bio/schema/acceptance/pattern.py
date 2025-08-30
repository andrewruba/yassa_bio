from pydantic import BaseModel
from typing import Optional
import pandas as pd

from yassa_bio.schema.layout.enum import SampleType, QCLevel


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    qc_level: Optional[QCLevel] = None
    needs_interferent: bool = False
    needs_matrix_type: bool = False
    carryover: bool = False
    needs_stability_condition: bool = False

    def mask(self, df: pd.DataFrame) -> pd.Series:
        m = df["sample_type"] == self.sample_type.value

        if self.qc_level is not None:
            m &= df["qc_level"] == self.qc_level.value

        if self.needs_interferent:
            m &= df["interferent"].notna()

        if self.needs_matrix_type:
            m &= df["matrix_type"].notna()
            m &= df["matrix_source_id"].notna()

        if self.carryover:
            m &= df["carryover"]

        if self.needs_stability_condition:
            m &= df["stability_condition"].notna()
            m &= df["stability_condition_time"].notna()

        return m

    def present(self, df: pd.DataFrame) -> bool:
        return self.mask(df).any()
