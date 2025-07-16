import pandas as pd
import numpy as np

from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_lloq_signal,
    compute_relative_pct_scalar,
    compute_relative_pct_vectorized,
)
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType


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


class TestGetLLOQSignal:
    def test_returns_none_on_empty(self):
        df = pd.DataFrame(columns=["concentration", "signal"])
        assert get_lloq_signal(df) is None

    def test_returns_mean_of_lowest_conc(self):
        df = pd.DataFrame(
            {
                "concentration": [10, 1, 1, 5],
                "signal": [100, 10, 20, 50],
            }
        )
        result = get_lloq_signal(df)
        assert result == 15.0  # mean of signals at concentration 1


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
        assert np.all(result[:2] == expected[:2])
        assert result[2] is None

    def test_pandas_series_input(self):
        nums = pd.Series([30, 0, 10])
        dens = pd.Series([60, 20, np.nan])
        result = compute_relative_pct_vectorized(nums, dens)
        expected = np.array([50.0, 0.0, None], dtype=object)
        assert np.all(result[:2] == expected[:2])
        assert result[2] is None

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
