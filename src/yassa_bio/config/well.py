from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Well(BaseModel):

    well: str = Field(
        ...,
        description=(
            "Canonical well ID in plate-notation, e.g. 'A1', 'H12', "
            "'AA24'.  Letters → row(s); number → column."
        ),
    )
    file_row: int = Field(
        ...,
        description=(
            "0-based *absolute* row index in the raw file where this well’s "
            "signal is located."
        ),
    )
    file_col: int = Field(
        ...,
        description=(
            "0-based *absolute* column index in the raw file where this well's "
            "signal is located."
        ),
    )

    sample_type: Literal["blank", "standard", "control", "sample", "spike"]
    replicate: Optional[int] = None
    level_idx: Optional[int] = Field(
        None, description="1-based position in the serial dilution (Std-1 → 1, …)."
    )
    dilution_factor: Optional[float] = Field(
        None, description="Fold change vs *previous* level (e.g. 2.0 for 1:2 dilution)."
    )
    concentration: Optional[float] = Field(
        None,
        description=(
            "Absolute concentration for this well; useful for overriding Series if provided."
        ),
    )
    units: Optional[str] = Field(
        None, description="Units for `concentration`, e.g. 'pg/mL' or 'ng/mL'."
    )

    exclude: bool = Field(
        False,
        description=("Set *True* to ignore this well in all downstream calculations."),
    )
    exclude_reason: Optional[str] = Field(
        None,
        description=("Brief explanation (≤ 5 words) for exclusion."),
    )
