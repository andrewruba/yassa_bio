import pandas as pd
import numpy as np
import pytest

from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_calibration_signal_for_level,
    compute_relative_pct_scalar,
    compute_relative_pct_vectorized,
)
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel, CalibrationLevel


class TestCheckRequiredWellPatterns:
    def test_all_present(self):
        df = pd.DataFrame({"sample_type": ["quality_control"]})
        patterns = [RequiredWellPattern(sample_type=SampleType.QUALITY_CONTROL)]
        assert check_required_well_patterns(df, patterns) == []

    def test_some_missing(self):
        df = pd.DataFrame({"sample_type": ["blank"]})
        patterns = [
            RequiredWellPattern(sample_type=SampleType.QUALITY_CONTROL),
            RequiredWellPattern(sample_type=SampleType.BLANK),
        ]
        missing = check_required_well_patterns(df, patterns)
        assert len(missing) == 1
        assert missing[0].sample_type == SampleType.QUALITY_CONTROL


class TestPatternErrorDict:
    def test_formats_message_and_dumps(self):
        pattern = RequiredWellPattern(sample_type=SampleType.BLANK)
        result = pattern_error_dict([pattern], "Missing {n} patterns")
        assert result["error"] == "Missing 1 patterns"
        assert result["pass"] is False
        assert isinstance(result["missing_patterns"], list)
        assert result["missing_patterns"][0]["sample_type"] == "blank"


class TestGetCalibrationSignalForLevel:
    def test_returns_none_on_empty(self):
        df = pd.DataFrame(columns=["concentration", "signal"])
        assert get_calibration_signal_for_level(df, QCLevel.LLOQ) is None

    def test_lloq_returns_mean_of_min_concentration(self):
        df = pd.DataFrame({"concentration": [10, 1, 1, 5], "signal": [100, 10, 20, 50]})
        result = get_calibration_signal_for_level(df, QCLevel.LLOQ)
        assert result == 15.0

        result = get_calibration_signal_for_level(df, CalibrationLevel.LLOQ)
        assert result == 15.0

    def test_uloq_returns_mean_of_max_concentration(self):
        df = pd.DataFrame({"concentration": [10, 10, 5], "signal": [200, 300, 50]})
        result = get_calibration_signal_for_level(df, QCLevel.ULOQ)
        assert result == 250.0

        result = get_calibration_signal_for_level(df, CalibrationLevel.ULOQ)
        assert result == 250.0

    def test_raises_on_unsupported_level(self):
        df = pd.DataFrame({"concentration": [1], "signal": [1]})

        class DummyLevel:
            value = "unsupported"

        with pytest.raises(ValueError):
            get_calibration_signal_for_level(df, DummyLevel())


class TestComputeRelativePctScalar:
    def test_normal_case(self):
        assert compute_relative_pct_scalar(50, 100) == 50.0

    def test_zero_numerator(self):
        assert compute_relative_pct_scalar(0, 100) == 0.0

    def test_zero_denominator(self):
        assert compute_relative_pct_scalar(50, 0) is None

    def test_none_denominator(self):
        assert compute_relative_pct_scalar(50, None) is None


class TestComputeRelativePctVectorized:
    def test_numpy_array_input(self):
        nums = np.array([50, 0, 100])
        dens = np.array([100, 10, 0])
        result = compute_relative_pct_vectorized(nums, dens)
        expected = np.array([50.0, 0.0, None], dtype=object)
        assert result.tolist() == expected.tolist()

    def test_pandas_series_input(self):
        nums = pd.Series([30, 0, 10])
        dens = pd.Series([60, 20, np.nan])
        result = compute_relative_pct_vectorized(nums, dens)
        expected = np.array([50.0, 0.0, None], dtype=object)
        assert result.tolist() == expected.tolist()

    def test_all_valid(self):
        nums = np.array([25, 50])
        dens = np.array([50, 100])
        result = compute_relative_pct_vectorized(nums, dens)
        assert result.tolist() == [50.0, 50.0]

    def test_all_invalid(self):
        nums = np.array([25, 50])
        dens = np.array([0, None])
        result = compute_relative_pct_vectorized(nums, dens)
        assert result.tolist() == [None, None]
