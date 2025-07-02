from enum import StrEnum, IntEnum


class PlateFormat(IntEnum):
    FMT_96 = 96
    FMT_384 = 384
    FMT_1536 = 1536


class SampleType(StrEnum):
    BLANK = "blank"
    STANDARD = "standard"
    CONTROL = "control"
    SAMPLE = "sample"
    SPIKE = "spike"


class QCLevel(StrEnum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"
    BLANK = "blank"
    ALL = "all"
    OTHER = "other"
