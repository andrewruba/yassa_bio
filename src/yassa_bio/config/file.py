from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class FileRef(BaseModel):
    filename: str = Field(
        ..., description="Exactly as uploaded; used as the key in look-ups."
    )
    sheet_index: int = Field(
        0,
        description=(
            "0-based sheet index when the export is a multi-sheet workbook.\n"
            "For single-sheet CSV/TXT files leave as 0."
        ),
    )
    delim: Optional[str] = Field(
        None,
        description="Explicit delimiter override (',' ';' '\\t'); auto-detected if None.",
    )
