from __future__ import annotations
from typing import List, Optional
from pydantic import Field, model_validator

from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.core.model import SchemaModel
from yassa_bio.core.enum import enum_examples
from yassa_bio.utils.standard import series_concentration_map


class PlateData(SchemaModel):
    """
    One *run* of data for a single plate.

    Links:
      • `source_file` – the PlateReaderFile that contains the raw signal values
      • `layout`      – the PlateLayout that tells us what each well means

    You can pass a PlateData directly into the analysis pipeline when all
    calibration/QC rules are satisfied on that plate alone.
    """

    source_file: PlateReaderFile = Field(
        ..., description="Raw reader-export that contains this plate’s numeric data."
    )
    plate_id: str = Field(
        ..., description="Barcode / run-name / UUID that uniquely identifies the plate."
    )
    layout: PlateLayout = Field(
        ..., description="Immutable map defining well roles and nominal values."
    )


class PlateLayout(SchemaModel):
    """
    *Layout* of a physical plate.

    * Describes where every well sits (row/col), its role (sample, QC, blank…),
      and any static metadata such as nominal concentration.
    * Re-used across many runs: today’s plate data and tomorrow’s can both be
      mapped with the same PlateLayout object.
    """

    sheet_index: int = Field(
        0,
        ge=0,
        description=(
            "0-based sheet index when the raw file is a multi-sheet XLS/X. "
            "For CSV/TXT leave as 0."
        ),
    )
    plate_format: PlateFormat = Field(
        PlateFormat.FMT_96,
        description="Well count of the plate.",
        examples=enum_examples(PlateFormat),
    )
    wells: List[WellTemplate]
    standards: Optional[StandardSeries] = Field(
        None,
        description=(
            "If not supplied, concentrations must be on each calibration standard Well."
        ),
    )

    @model_validator(mode="after")
    def _resolve_standard_concs(self):
        if self.standards is None:
            return self

        series_map = series_concentration_map(self.standards)

        for w in self.wells:
            if w.sample_type is not SampleType.CALIBRATION_STANDARD:
                continue

            if w.concentration is not None:
                continue

            if w.level_idx is None or w.level_idx not in series_map:
                raise ValueError(
                    f"{w.well}: level_idx missing or > num_levels="
                    f"{self.standards.num_levels}"
                )

            w.concentration = series_map[w.level_idx]
            w.concentration_units = self.standards.concentration_units

        return self
