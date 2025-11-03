from pydantic import BaseModel
from typing import Optional
import pandas as pd

from yassa_bio.schema.layout.enum import SampleType, QCLevel


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    qc_level: Optional[QCLevel] = None

    def mask(self, df: pd.DataFrame) -> pd.Series:
        m = df["sample_type"] == self.sample_type.value

        if self.qc_level is not None:
            m &= df["qc_level"] == self.qc_level.value

        return m

    def present(self, df: pd.DataFrame) -> bool:
        return self.mask(df).any()
