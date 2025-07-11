import pandas as pd

from yassa_bio.evaluation.analysis.engine.normalize import (
    _norm_span,
    _norm_max,
    _norm_none,
)


class TestNormSpan:
    def test_span_typical(self):
        df = pd.DataFrame(
            {
                "sample_type": ["calibration_standard"] * 3,
                "concentration": [10, 20, 30],
                "signal": [15, 25, 35],
            }
        )
        normalized, span = _norm_span(df)
        expected = (df["signal"] - 10) / 20
        pd.testing.assert_series_equal(normalized, expected)
        assert span == 20

    def test_span_empty_calibration(self):
        df = pd.DataFrame(
            {
                "sample_type": ["sample"] * 3,
                "concentration": [0, 0, 0],
                "signal": [1, 2, 3],
            }
        )
        normalized, span = _norm_span(df)
        pd.testing.assert_series_equal(normalized, df["signal"])
        assert span is None

    def test_span_zero_span(self):
        df = pd.DataFrame(
            {
                "sample_type": ["calibration_standard"] * 3,
                "concentration": [5, 5, 5],
                "signal": [2, 3, 4],
            }
        )
        normalized, span = _norm_span(df)
        pd.testing.assert_series_equal(normalized, df["signal"])
        assert span is None


class TestNormMax:
    def test_max_typical(self):
        df = pd.DataFrame(
            {
                "sample_type": ["calibration_standard"] * 3,
                "concentration": [5, 10, 20],
                "signal": [1, 2, 3],
            }
        )
        normalized, maxv = _norm_max(df)
        expected = df["signal"] / 20
        pd.testing.assert_series_equal(normalized, expected)
        assert maxv == 20

    def test_max_empty_calibration(self):
        df = pd.DataFrame(
            {
                "sample_type": ["sample"] * 3,
                "concentration": [1, 2, 3],
                "signal": [4, 5, 6],
            }
        )
        normalized, maxv = _norm_max(df)
        pd.testing.assert_series_equal(normalized, df["signal"])
        assert maxv is None

    def test_max_zero(self):
        df = pd.DataFrame(
            {
                "sample_type": ["calibration_standard"] * 3,
                "concentration": [0, 0, 0],
                "signal": [4, 5, 6],
            }
        )
        normalized, maxv = _norm_max(df)
        pd.testing.assert_series_equal(normalized, df["signal"])
        assert maxv is None


class TestNormNone:
    def test_none_passthrough(self):
        df = pd.DataFrame(
            {
                "sample_type": ["sample"] * 3,
                "concentration": [0, 0, 0],
                "signal": [7, 8, 9],
            }
        )
        normalized, flag = _norm_none(df)
        pd.testing.assert_series_equal(normalized, df["signal"])
        assert flag is None
