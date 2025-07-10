import numpy as np

from yassa_bio.evaluation.analysis.engine.blank import (
    _blank_mean,
    _blank_median,
    _blank_min,
    _blank_none,
)


class TestBlankMean:
    def test_mean_typical(self):
        vals = np.array([1.0, 2.0, 3.0, 4.0])
        mask = np.array([False, True, True, False])
        assert _blank_mean(vals, mask) == 2.5

    def test_mean_all_false(self):
        assert _blank_mean(np.array([1.0, 2.0]), np.array([False, False])) is None

    def test_mean_one_value(self):
        assert _blank_mean(np.array([5.0]), np.array([True])) == 5.0

    def test_mean_with_nans(self):
        vals = np.array([np.nan, 2.0, 4.0])
        mask = np.array([True, True, False])
        assert np.isnan(_blank_mean(vals, mask))

    def test_mean_all_same(self):
        assert (
            _blank_mean(np.array([3.0, 3.0, 3.0]), np.array([True, True, True])) == 3.0
        )


class TestBlankMedian:
    def test_median_typical(self):
        vals = np.array([1.0, 3.0, 2.0])
        mask = np.array([True, False, True])
        assert _blank_median(vals, mask) == 1.5

    def test_median_empty(self):
        assert _blank_median(np.array([5.0, 6.0]), np.array([False, False])) is None

    def test_median_single(self):
        assert _blank_median(np.array([7.0]), np.array([True])) == 7.0

    def test_median_all_same(self):
        assert (
            _blank_median(np.array([9.0, 9.0, 9.0]), np.array([True, True, True]))
            == 9.0
        )


class TestBlankMin:
    def test_min_typical(self):
        vals = np.array([8.0, 1.0, 5.0])
        mask = np.array([False, True, True])
        assert _blank_min(vals, mask) == 1.0

    def test_min_all_false(self):
        assert _blank_min(np.array([3.0, 2.0]), np.array([False, False])) is None

    def test_min_single(self):
        assert _blank_min(np.array([10.0]), np.array([True])) == 10.0

    def test_min_with_nans(self):
        vals = np.array([np.nan, 1.0])
        mask = np.array([True, True])
        result = _blank_min(vals, mask)
        assert np.isnan(result) or result == 1.0


class TestBlankNone:
    def test_none_returns_none(self):
        assert _blank_none(np.array([1.0, 2.0]), np.array([True, False])) is None

    def test_none_empty(self):
        assert _blank_none(np.array([]), np.array([])) is None
