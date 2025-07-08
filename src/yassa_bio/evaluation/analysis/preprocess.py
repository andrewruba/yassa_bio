import pandas as pd
from dataclasses import dataclass

from yassa_bio.schema.analysis.preprocess import Preprocess
from yassa_bio.core.registry import get


@dataclass(slots=True)
class PrepResult:
    df: pd.DataFrame  # original columns + clean_signal, is_outlier
    blank_used: float | None
    norm_span: float | None


def preprocess(
    df: pd.DataFrame,
    cfg: Preprocess,
    *,
    signal_col: str = "signal",
    plate_id: str | None = None,
) -> PrepResult:
    # ----- slice & copy --------------------------------------------------- #
    df = df[df["plate_id"] == plate_id].copy() if plate_id else df.copy()

    # ----- blank subtraction --------------------------------------------- #
    blank_mask = df["sample_type"].eq("blank")
    blank_fn = get("blank_rule", cfg.blank_rule)
    blank_val = blank_fn(df[signal_col].to_numpy(float), blank_mask.to_numpy())
    clean = df[signal_col].astype(float)
    if blank_val is not None:
        clean -= blank_val

    df["signal_bs"] = clean  # keep intermediate for curiosity/debug

    # ----- normalisation -------------------------------------------------- #
    norm_fn = get("norm_rule", cfg.norm_rule)
    clean, span = norm_fn(df.assign(signal=clean))  # function returns Series

    df["clean_signal"] = clean

    # ----- outliers ------------------------------------------------------- #
    outlier_fn = get("outlier_rule", cfg.outliers.rule)
    df["is_outlier"] = outlier_fn(df["clean_signal"].to_numpy(float), cfg.outliers)

    return PrepResult(df=df, blank_used=blank_val, norm_span=span)
