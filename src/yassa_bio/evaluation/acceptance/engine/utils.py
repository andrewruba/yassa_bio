import pandas as pd
import numpy as np

from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


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


def get_lloq_signal(calib_df: pd.DataFrame) -> float | None:
    if calib_df.empty:
        return None
    lloq_conc = calib_df["concentration"].min()
    return calib_df[calib_df["concentration"] == lloq_conc]["signal"].mean()


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
