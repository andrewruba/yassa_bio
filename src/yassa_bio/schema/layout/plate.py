from __future__ import annotations
from typing import List, Optional
from pydantic import Field, model_validator

from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.core.model import SchemaModel
from yassa_bio.core.enum import enum_examples
from yassa_bio.utils.standard import series_concentration_map


class Plate(SchemaModel):
    """One physical plate with its wells."""

    plate_id: str = Field(
        ...,
        description="Stable identifier: barcode, run name, or UUID.",
    )
    sheet_index: int = Field(
        0,
        ge=0,
        description=(
            "0-based sheet index when the raw file is a multi-sheet XLS/X. "
            "For CSV/TXT leave as 0."
        ),
    )
    plate_format: PlateFormat = Field(
        default=PlateFormat.FMT_96,
        description="Well count of the plate.",
        examples=enum_examples(PlateFormat),
    )
    wells: List[Well]
    standards: Optional[StandardSeries] = Field(
        None,
        description=(
            "If not supplied, concentrations must be on each calibration standard Well."
        ),
    )

    @model_validator(mode="after")
    def _check_standard_concentrations(self):
        series_map = series_concentration_map(self.standards) if self.standards else {}

        errors = []
        for w in self.wells:
            if w.sample_type is SampleType.CALIBRATION_STANDARD:
                has_override = w.concentration is not None
                has_series = series_map.get(w.level_idx or -1) is not None
                if not (has_override or has_series):
                    errors.append(
                        f"{w.well}: calibration standard missing concentration "
                        "(no StandardSeries match and no per-well override)"
                    )
            else:
                if w.concentration is None and w.level_idx is not None:
                    errors.append(
                        f"{w.well}: level_idx set but this sample type "
                        "is not a calibration standard"
                    )

        if errors:
            raise ValueError(" ; ".join(errors))
        return self
