from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class FileRef(BaseModel):
    """Pointer to a raw plate-reader export on disk, S3, GCS, etc."""

    filename: str = Field(
        ...,
        description="Exact file name as uploaded; used as a lookup key.",
    )
    sheet_index: int = Field(
        0,
        description=(
            "0-based sheet index when the file is a multi-sheet XLS/X. "
            "For CSV/TXT leave as 0."
        ),
    )
    delim: Optional[str] = Field(
        None,
        description=(
            "Explicit delimiter override (',', ';', or '\\t'). "
            "If None the parser will auto-detect."
        ),
    )
