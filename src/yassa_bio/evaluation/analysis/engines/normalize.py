import pandas as pd

from yassa_bio.schema.analysis.enum import NormRule
from yassa_bio.core.registry import register


@register("norm_rule", NormRule.SPAN)
def _norm_span(df: pd.DataFrame) -> tuple[pd.Series, float | None]:
    cal = df.query("sample_type == 'calibration_standard'")
    if cal.empty:
        return df["signal_raw"], None
    low = cal["concentration"].min()
    high = cal["concentration"].max()
    span = high - low
    if not span:
        return df["signal_raw"], None
    return (df["signal_raw"] - low) / span, span


@register("norm_rule", NormRule.MAX)
def _norm_max(df: pd.DataFrame) -> tuple[pd.Series, float | None]:
    cal = df.query("sample_type == 'calibration_standard'")
    if cal.empty:
        return df["signal_raw"], None
    maxv = cal["concentration"].max()
    if not maxv:
        return df["signal_raw"], None
    return df["signal_raw"] / maxv, maxv


@register("norm_rule", NormRule.NONE)
def _norm_none(df: pd.DataFrame) -> tuple[pd.Series, None]:
    return df["signal_raw"], None
