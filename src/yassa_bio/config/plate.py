from __future__ import annotations
from typing import Literal, List
from pydantic import BaseModel
from yassa_bio.config.file import FileRef
from yassa_bio.config.well import Well


class Plate(BaseModel):
    plate_id: str
    file: FileRef
    plate_format: Literal[96, 384, 1536] = 96
    wells: List[Well]
