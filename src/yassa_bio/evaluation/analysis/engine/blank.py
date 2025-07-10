import numpy as np

from yassa_bio.schema.analysis.enum import BlankRule
from yassa_bio.core.registry import register


@register("blank_rule", BlankRule.MEAN)
def _blank_mean(vals: np.ndarray, mask: np.ndarray) -> float | None:
    m = vals[mask]
    return float(m.mean()) if m.size else None


@register("blank_rule", BlankRule.MEDIAN)
def _blank_median(vals: np.ndarray, mask: np.ndarray) -> float | None:
    m = vals[mask]
    return float(np.median(m)) if m.size else None


@register("blank_rule", BlankRule.MINIMUM)
def _blank_min(vals: np.ndarray, mask: np.ndarray) -> float | None:
    m = vals[mask]
    return float(m.min()) if m.size else None


@register("blank_rule", BlankRule.NONE)
def _blank_none(vals: np.ndarray, mask: np.ndarray) -> None:
    return None
