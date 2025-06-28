from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Well(BaseModel):
    """Map one physical well to its location in the raw data table."""

    well: str = Field(
        ...,
        description="Canonical ID (e.g. 'A1', 'H12', 'AA24').",
    )
    file_row: int = Field(
        ...,
        description="0-based absolute row index in the raw file.",
    )
    file_col: int = Field(
        ...,
        description="0-based absolute column index in the raw file.",
    )

    sample_type: Literal["blank", "standard", "control", "sample", "spike"] = Field(
        ...,
        description="High-level role of this well in the assay.",
    )
    replicate: Optional[int] = Field(
        None,
        description="1-based replicate counter inside a group; leave None if N/A.",
    )
    level_idx: Optional[int] = Field(
        None,
        description="Serial-dilution position (Std-1 → 1, Std-2 → 2, …).",
    )
    dilution_factor: Optional[float] = Field(
        None,
        description="Fold change vs *preceding* level (e.g. 2.0 for a 1:2 dilution).",
    )
    concentration: Optional[float] = Field(
        None,
        description="Absolute concentration override for this individual well.",
    )
    units: Optional[str] = Field(
        None,
        description="Units for `concentration`, e.g. 'pg/mL' or 'ng/mL'.",
    )

    exclude: bool = Field(
        False,
        description="Mark True to drop this well from all downstream calculations.",
    )
    exclude_reason: Optional[str] = Field(
        None,
        description="≤ 5-word reason for exclusion (e.g. 'bubble', 'edge leak').",
    )
