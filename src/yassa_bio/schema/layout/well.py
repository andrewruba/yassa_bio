from __future__ import annotations
import re
from typing import Optional
from pydantic import Field, model_validator, field_validator

from yassa_bio.schema.layout.enum import SampleType, QcLevel
from yassa_bio.core.model import SchemaModel


class Well(SchemaModel):
    """Map one physical well to its location in the raw data table."""

    well: str = Field(
        ...,
        description="Canonical ID (e.g. 'A1', 'H12', 'AA24').",
        examples=["A1", "H12", "AA24"],
    )
    file_row: int = Field(
        ...,
        ge=0,
        description="0-based absolute row index in the raw file.",
    )
    file_col: int = Field(
        ...,
        ge=0,
        description="0-based absolute column index in the raw file.",
    )

    sample_type: SampleType = Field(
        ...,
        description="High-level role of this well in the assay.",
    )
    qc_level: Optional[QcLevel] = Field(
        None,
        description=(
            "QC band for CONTROL or SPIKE wells. "
            "Leave blank when the assay has only one global tolerance band."
        ),
    )
    replicate: Optional[int] = Field(
        None,
        ge=1,
        description="1-based replicate counter inside a group; leave None if N/A.",
    )
    level_idx: Optional[int] = Field(
        None,
        ge=1,
        description="Serial-dilution position (Std-1 → 1, Std-2 → 2, …).",
    )
    dilution_factor: Optional[float] = Field(
        None,
        gt=1,
        description="Fold change vs *preceding* level (e.g. 2.0 for a 1:2 dilution).",
    )
    concentration: Optional[float] = Field(
        None,
        description="Absolute concentration override for this individual well.",
    )
    concentration_units: Optional[str] = Field(
        None,
        description=(
            "Units for the concentration override (e.g. 'ng/mL'). "
            "Required if `concentration` is set."
        ),
        examples=["ng/mL", "pg/mL", "mU/mL", "IU/mL"],
    )

    exclude: bool = Field(
        False,
        description="Mark True to drop this well from all downstream calculations.",
    )
    exclude_reason: Optional[str] = Field(
        None,
        description=(
            "≤ 5-word reason for exclusion (e.g. 'bubble', 'edge leak'). "
            "Required if `exclude` is True."
        ),
    )

    @model_validator(mode="after")
    def _reason_required_if_excluded(self):
        if self.exclude and not self.exclude_reason:
            raise ValueError("exclude_reason must be provided whenever exclude is True")
        return self

    @model_validator(mode="after")
    def _units_required_if_concentration(self):
        if (self.concentration is not None) != (self.concentration_units is not None):
            raise ValueError(
                "'concentration' and 'concentration_units' must be provided together"
            )
        return self

    @field_validator("well", mode="before")
    @classmethod
    def _validate_well_id(cls, v: str) -> str:
        v = v.strip().upper()
        _WELL_ID_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")
        if not _WELL_ID_RE.fullmatch(v):
            raise ValueError(
                "well must match plate notation like 'A1', 'H12', 'AA24' "
                "(letters followed by a non-zero column number)"
            )
        return v

    @model_validator(mode="after")
    def _qc_level_allowed_for_type(self):
        if (
            self.sample_type not in {SampleType.CONTROL, SampleType.SPIKE}
            and self.qc_level
        ):
            raise ValueError("qc_level only valid on CONTROL or SPIKE wells")
        return self
