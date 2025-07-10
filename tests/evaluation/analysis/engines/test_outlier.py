import numpy as np

from yassa_bio.schema.analysis.preprocess import OutlierParams
from yassa_bio.evaluation.analysis.engine.outlier import (
    _mask_zscore,
    _mask_grubbs,
    _mask_iqr,
    _mask_none,
)


class TestZScore:
    def test_flags_above_threshold(self):
        vals = np.array([1, 1, 1, 1, 1, 10])
        p = OutlierParams(rule="zscore", z_threshold=2.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_zscore(vals, p)
        assert np.sum(mask) == 1
        assert mask[-1]

    def test_no_outliers(self):
        vals = np.array([1, 2, 3, 4])
        p = OutlierParams(rule="zscore", z_threshold=5.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_zscore(vals, p)
        assert not np.all(mask)

    def test_zscore_zero_std(self):
        vals = np.array([3, 3, 3])
        p = OutlierParams(rule="zscore", z_threshold=1.0, grubbs_alpha=0.05, iqr_k=1.5)
        # ignore expected divide by zero warning
        with np.errstate(invalid="ignore"):
            mask = _mask_zscore(vals, p)
        assert not np.all(mask)


class TestGrubbs:
    def test_small_sample_returns_all_false(self):
        vals = np.array([1, 10])
        p = OutlierParams(rule="grubbs", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_grubbs(vals, p)
        assert not np.all(mask)

    def test_detects_grubbs_outlier(self):
        vals = np.array([10, 11, 12, 50])
        p = OutlierParams(rule="grubbs", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_grubbs(vals, p)
        assert mask[-1]

    def test_grubbs_no_outliers(self):
        vals = np.array([10, 11, 10, 11])
        p = OutlierParams(rule="grubbs", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_grubbs(vals, p)
        assert np.sum(mask) == 0


class TestIQR:
    def test_detects_outliers(self):
        vals = np.array([10, 12, 13, 14, 15, 100])
        p = OutlierParams(rule="iqr", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_iqr(vals, p)
        assert mask[-1]

    def test_no_outliers_if_inside_range(self):
        vals = np.array([1, 2, 3, 4, 5])
        p = OutlierParams(rule="iqr", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_iqr(vals, p)
        assert not np.all(mask)

    def test_iqr_zero_range(self):
        vals = np.array([5, 5, 5, 5])
        p = OutlierParams(rule="iqr", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_iqr(vals, p)
        assert not np.all(mask)


class TestNoneRule:
    def test_all_false(self):
        vals = np.array([10, 100, 3])
        p = OutlierParams(rule="none", z_threshold=3.0, grubbs_alpha=0.05, iqr_k=1.5)
        mask = _mask_none(vals, p)
        assert not np.all(mask)
