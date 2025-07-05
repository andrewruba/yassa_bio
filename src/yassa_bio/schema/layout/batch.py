from __future__ import annotations
from typing import List
from pydantic import Field, model_validator

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.plate import Plate


class Batch(SchemaModel):
    """
    Atomic analysis unit – the smallest collection of data that will be
    processed and judged against one set of acceptance criteria.

    For method validation, a batch usually one plate (or a group
      of plates measured together) that satisfies a single validation spec
      (e.g. Carry-over, Parallelism, Stability).
    For routine sample analysis, a batch is often a logical set of
      plates sharing the same calibration/QC context.
    """

    files: dict[str, PlateReaderFile] = Field(
        ...,
        description=(
            "Lookup table of the raw plate-reader files used by plates in this batch"
        ),
    )
    plates: List[Plate] = Field(
        ..., description="One entry per physical plate in the raw file."
    )

    @model_validator(mode="after")
    def _validate_plate_file_links(self):
        unknown = [p.file_key for p in self.plates if p.file_key not in self.files]
        if unknown:
            raise ValueError(
                "Plates reference unknown file_key(s): "
                + ", ".join(sorted(set(unknown)))
            )
        return self
