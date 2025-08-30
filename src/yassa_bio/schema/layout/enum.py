from enum import IntEnum

from yassa_bio.core.enum import DescribedStrEnum


class PlateFormat(IntEnum):
    FMT_6 = 6
    FMT_12 = 12
    FMT_24 = 24
    FMT_48 = 48
    FMT_96 = 96
    FMT_384 = 384
    FMT_1536 = 1536
    FMT_3456 = 3456


class SampleType(DescribedStrEnum):
    BLANK = ("blank", "Matrix only – no analyte or internal standard")
    CALIBRATION_STANDARD = (
        "calibration_standard",
        "Known-concentration standards that define the curve (Std-1 … Std-N)",
    )
    INTERNAL_STANDARD = ("internal_standard", "IS-only well (carry-over / drift check)")
    ZERO_STANDARD = ("zero_standard", "0-conc standard: matrix + IS, no analyte")
    ANCHOR_STANDARD = (
        "anchor_standard",
        "Extra point <LLOQ or >ULOQ, stabilises 4-/5-PL fit; excluded from stats",
    )
    QUALITY_CONTROL = (
        "quality_control",
        "Independent QC sample (LLOQ, low, mid, high, ULOQ, above ULOQ)",
    )
    SAMPLE = ("sample", "Study / incurred sample well")


class QCLevel(DescribedStrEnum):
    LLOQ = ("lloq", "QC at lower-limit of quantification")
    LOW = ("low", "≈ 3 × LLOQ QC")
    MID = ("mid", "Geometric-mean / mid-range QC")
    HIGH = ("high", "≈ 75 % ULOQ QC")
    ULOQ = ("uloq", "QC at upper-limit of quantification")
    ABOVE_ULOQ = ("above_uloq", "QC level above the upper-limit of quantification")


class CalibrationLevel(DescribedStrEnum):
    LLOQ = ("lloq", "Calibration standard at lower-limit of quantification")
    ULOQ = ("uloq", "Calibration standard at upper-limit of quantification")


class StabilityConditionTime(DescribedStrEnum):
    BEFORE = ("before", "Time point before stability condition is applied")
    AFTER = ("after", "Time point after stability condition is applied")
