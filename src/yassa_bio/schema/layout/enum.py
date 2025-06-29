from enum import StrEnum, IntEnum


class PlateFormat(IntEnum):
    """Allowed well counts for microplates."""

    FMT_96 = 96
    FMT_384 = 384
    FMT_1536 = 1536


class SampleType(StrEnum):
    """High-level role of a well in the assay."""

    BLANK = "blank"
    STANDARD = "standard"
    CONTROL = "control"
    SAMPLE = "sample"
    SPIKE = "spike"
