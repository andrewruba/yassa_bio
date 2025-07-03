from enum import StrEnum, IntEnum


class PlateFormat(IntEnum):
    FMT_96 = 96
    FMT_384 = 384
    FMT_1536 = 1536


class SampleType(StrEnum):
    BLANK = "blank"
    CALIBRATION_STANDARD = "calibration_standard"
    INTERNAL_STANDARD = "internal_standard"
    ZERO_STANDARD = "zero_standard"
    ANCHOR_STANDARD = "anchor_standard"
    QUALITY_CONTROL = "quality_control"
    SAMPLE = "sample"


class QCLevel(StrEnum):
    LLOQ = "lloq"
    LOW = "low"
    MID = "mid"
    HIGH = "high"
    ULOQ = "uloq"
