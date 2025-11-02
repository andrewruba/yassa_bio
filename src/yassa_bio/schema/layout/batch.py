from __future__ import annotations
from typing import List, Optional
from pydantic import Field, PrivateAttr
import pandas as pd

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.layout.plate import PlateData


class BatchData(SchemaModel):
    """
    A *batch* = collection of plates whose data are evaluated together.

    Typical uses
    ────────────
    • **Routine run** – multiple plates from the same study day that share
      a calibration curve / QC bracket.
    """

    plates: List[PlateData] = Field(
        ..., description="All plates whose results will be combined for acceptance."
    )

    _df: Optional[pd.DataFrame] = PrivateAttr(None)
    _mtimes: Optional[dict[str, float]] = PrivateAttr(None)

    @property
    def df(self) -> pd.DataFrame:
        current_mtimes = {
            p.plate_id: p.source_file.path.stat().st_mtime for p in self.plates
        }
        if self._df is not None and self._mtimes == current_mtimes:
            return self._df

        frames: list[pd.DataFrame] = []
        for p in self.plates:
            df_plate = p.df.copy()
            frames.append(df_plate)

        self._df = pd.concat(frames, ignore_index=True)
        self._mtimes = current_mtimes
        return self._df
