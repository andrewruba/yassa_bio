import pandas as pd
import numpy as np

from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import QCLevel, CalibrationLevel


def check_required_well_patterns(
    df: pd.DataFrame, patterns: list[RequiredWellPattern]
) -> list[RequiredWellPattern]:
    return [p for p in patterns if not p.present(df)]


def pattern_error_dict(missing: list[RequiredWellPattern], msg: str) -> dict:
    return {
        "error": msg.format(n=len(missing)),
        "missing_patterns": [p.model_dump() for p in missing],
        "pass": False,
    }


def get_calibration_signal_for_level(
    calib_df: pd.DataFrame, level: QCLevel | CalibrationLevel
) -> float | None:
    """
    Returns the mean signal at the calibration concentration corresponding to the
    LLOQ or ULOQ, regardless of whether the input is a QCLevel or CalibrationLevel.
    """
    if calib_df.empty:
        return None

    if level.value == "lloq":
        target_conc = calib_df["concentration"].min()
    elif level.value == "uloq":
        target_conc = calib_df["concentration"].max()
    else:
        raise ValueError(f"Unsupported level for calibration lookup: {level}")

    return calib_df[calib_df["concentration"] == target_conc]["signal"].mean()


def get_calibration_concentration_for_level(
    calib_df: pd.DataFrame, level: QCLevel | CalibrationLevel
) -> float | None:
    """
    Returns the concentration corresponding to LLOQ or ULOQ in the calibration data.
    """
    if calib_df.empty:
        return None

    if level.value == "lloq":
        return calib_df["concentration"].min()
    elif level.value == "uloq":
        return calib_df["concentration"].max()
    else:
        raise ValueError(f"Unsupported level for calibration lookup: {level}")


def compute_relative_pct_scalar(
    numerator: float, denominator: float | None
) -> float | None:
    return (numerator / denominator * 100.0) if denominator else None


def compute_relative_pct_vectorized(
    numerator: pd.Series | np.ndarray,
    denominator: pd.Series | np.ndarray,
) -> np.ndarray:
    """
    Element-wise compute (numerator / denominator * 100),
    with None if denominator is 0 or null.
    Returns a NumPy array of dtype=object containing floats or None.
    """
    numerator = np.asarray(numerator)
    denominator = np.asarray(denominator)

    result = np.empty_like(numerator, dtype=object)
    mask_valid = (denominator != 0) & ~pd.isna(denominator)
    result[mask_valid] = (numerator[mask_valid] / denominator[mask_valid]) * 100.0
    result[~mask_valid] = None
    return result
