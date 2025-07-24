from pydantic import BaseModel, Field
from typing import Optional


class CellFormat(BaseModel):
    """
    Optional per-cell formatting metadata for table display.
    """

    digits: Optional[int] = Field(
        default=None,
        description=(
            "Number of digits to display for this cell, overrides column-wide digits."
        ),
        ge=0,
    )
    format_string: Optional[str] = Field(
        default=None,
        description="Full format string (e.g., '{:.2f}', '{:,.1f}') for the cell.",
    )
    bold: bool = Field(default=False, description="Render the cell in bold.")
    italic: bool = Field(default=False, description="Render the cell in italics.")
    color: Optional[str] = Field(
        default=None, description="Optional text color (e.g., 'red', '#333')."
    )
    tooltip: Optional[str] = Field(
        default=None, description="Tooltip text shown on hover (HTML only)."
    )
