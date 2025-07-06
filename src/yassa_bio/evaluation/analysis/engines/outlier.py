import numpy as np
from scipy import stats

from yassa_bio.schema.analysis.preprocess import OutlierParams
from yassa_bio.schema.analysis.enum import OutlierRule
from yassa_bio.core.registry import register


@register("outlier_rule", OutlierRule.ZSCORE)
def _mask_zscore(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    z = np.abs((vals - vals.mean()) / vals.std(ddof=1))
    return z > p.z_threshold


@register("outlier_rule", OutlierRule.GRUBBS)
def _mask_grubbs(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    n = len(vals)
    if n < 3:
        return np.zeros_like(vals, dtype=bool)

    mean = vals.mean()
    sd = vals.std(ddof=1)
    G = np.abs(vals - mean) / sd

    # critical value (two-sided)  –  G_crit = ((n-1)/√n) * √(t²/(n-2+t²))
    t = stats.t.ppf(1 - p.grubbs_alpha / (2 * n), n - 2)
    Gcrit = ((n - 1) / np.sqrt(n)) * np.sqrt(t**2 / (n - 2 + t**2))

    return G > Gcrit


@register("outlier_rule", OutlierRule.ROSNER)
def _mask_rosner(vals: np.ndarray, p: OutlierParams) -> np.ndarray:
    """
    Very small, fast implementation of Rosner’s test (generalised ESD)
    that flags **up to 10% of points or 10 points** – whichever is smaller.
    """
    x = vals.copy()
    n = len(x)
    k_max = min(int(0.1 * n), 10)  # practical upper cap
    mask = np.zeros(n, dtype=bool)
    removed = []

    for k in range(1, k_max + 1):
        mean = x[~mask].mean()
        sd = x[~mask].std(ddof=1)
        if sd == 0:
            break
        R = np.abs(x - mean) / sd
        i = np.argmax(R)
        R_i = R[i]

        # critical value for this step
        t = stats.t.ppf(1 - p.grubbs_alpha / (2 * (n - k + 1)), n - k - 1)
        lam_k = ((n - k) * t) / np.sqrt((n - k - 1 + t**2) * (n - k + 1))

        if R_i > lam_k:
            mask[i] = True
            removed.append(i)
        else:
            break
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
