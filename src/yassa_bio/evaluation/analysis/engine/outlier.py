import numpy as np
from outliers import smirnov_grubbs as grubbs

from yassa_bio.schema.analysis.preprocess import OutlierParams
from yassa_bio.schema.analysis.enum import OutlierRule
from yassa_bio.core.registry import register


@register("outlier_rule", OutlierRule.ZSCORE)
def _mask_zscore(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    z = np.abs((vals - vals.mean()) / vals.std(ddof=1))
    return z > p.z_threshold


@register("outlier_rule", OutlierRule.GRUBBS)
def _mask_grubbs(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    if len(vals) < 3:
        return np.zeros_like(vals, dtype=bool)

    indices = grubbs.two_sided_test_indices(vals, alpha=p.grubbs_alpha)
    mask = np.zeros_like(vals, dtype=bool)
    mask[indices] = True
    return mask


@register("outlier_rule", OutlierRule.IQR)
def _mask_iqr(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    q1, q3 = np.percentile(vals, [25, 75])
    iqr = q3 - q1
    lo = q1 - p.iqr_k * iqr
    hi = q3 + p.iqr_k * iqr
    return (vals < lo) | (vals > hi)


@register("outlier_rule", OutlierRule.NONE)
def _mask_none(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    return np.zeros_like(vals, dtype=bool)
