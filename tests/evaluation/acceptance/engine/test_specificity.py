import pytest
import pandas as pd

from yassa_bio.evaluation.acceptance.engine.specificity import (
    eval_specificity,
    compute_interferent_accuracy,
)
from yassa_bio.schema.acceptance.validation.specificity import SpecificitySpec
from yassa_bio.schema.layout.enum import QCLevel


class TestComputeInterferentAccuracy:
    def test_normal_case(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 4,
                "qc_level": ["lloq"] * 4,
                "interferent": [None, None, "X", "X"],
                "signal": [95, 105, 120, 130],
            }
        )

        result = compute_interferent_accuracy(df, QCLevel.LLOQ)

        assert result["accuracy_pct"] == pytest.approx(25.0)
        assert result["clean_n"] == 2
        assert result["interfered_n"] == 2
        assert result["pass"] is None
        assert result["interferents"] == ["X"]

    def test_empty_interfered(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 2,
                "qc_level": ["lloq"] * 2,
                "interferent": [None, None],
                "signal": [100, 100],
            }
        )
        result = compute_interferent_accuracy(df, QCLevel.LLOQ)
        assert result is None

    def test_empty_clean(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 2,
                "qc_level": ["uloq"] * 2,
                "interferent": ["A", "B"],
                "signal": [200, 220],
            }
        )
        result = compute_interferent_accuracy(df, QCLevel.ULOQ)
        assert result is None


class TestEvalSpecificity:
    def make_ctx(self, df: pd.DataFrame, calib_df: pd.DataFrame):
        class DummyCtx:
            def __init__(self, df, calib_df):
                self.data = df
                self.calib_df = calib_df

        return DummyCtx(df, calib_df)

    def test_valid_pass_case(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank", "quality_control", "quality_control"] * 2,
                "qc_level": [None, "lloq", "uloq"] * 2,
                "interferent": ["X", "X", "X", None, None, None],
                "signal": [2, 100, 200, None, 95, 205],
            }
        )
        calib_df = pd.DataFrame(
            {
                "concentration": [1, 1, 2, 2, 5],
                "signal": [20, 20, 50, 52, 100],
            }
        )
        spec = SpecificitySpec()
        ctx = self.make_ctx(df, calib_df)

        result = eval_specificity(ctx, spec)
        assert result["blank_pass"]
        assert result["lloq_accuracy"]["pass"]
        assert result["uloq_accuracy"]["pass"]
        assert result["pass"]

    def test_missing_required_patterns(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"],
                "qc_level": [None],
                "interferent": ["X"],
                "signal": [5],
            }
        )
        calib_df = pd.DataFrame(
            {
                "concentration": [1],
                "signal": [20],
            }
        )
        ctx = self.make_ctx(df, calib_df)
        spec = SpecificitySpec()

        result = eval_specificity(ctx, spec)
        assert result["pass"] is False
        assert "missing_patterns" in result
        assert result["error"].startswith("Missing")

    def test_blank_fails_threshold(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"],
                "interferent": ["X"],
                "signal": [30],
            }
        )
        calib_df = pd.DataFrame(
            {
                "concentration": [1],
                "signal": [20],
            }
        )
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    {
                        "sample_type": ["quality_control"] * 4,
                        "qc_level": ["lloq"] * 2 + ["uloq"] * 2,
                        "interferent": ["X", None, "X", None],
                        "signal": [100, 90, 200, 210],
                    }
                ),
            ],
            ignore_index=True,
        )

        ctx = self.make_ctx(df, calib_df)
        spec = SpecificitySpec()

        result = eval_specificity(ctx, spec)

        assert not result["blank_pass"]
        assert not result["pass"]

    def test_accuracy_fails(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank", "quality_control", "quality_control"] * 2,
                "qc_level": [None, "lloq", "uloq"] * 2,
                "interferent": ["X", "X", "X", None, None, None],
                "signal": [5, 100, 300, None, 90, 100],
            }
        )
        calib_df = pd.DataFrame(
            {
                "concentration": [1],
                "signal": [20],
            }
        )
        ctx = self.make_ctx(df, calib_df)
        spec = SpecificitySpec()

        result = eval_specificity(ctx, spec)

        assert not result["uloq_accuracy"]["pass"]
        assert not result["pass"]

    def test_insufficient_data_sets_error_flag(self, mocker):
        df = pd.DataFrame(
            {
                "sample_type": ["blank", "quality_control", "quality_control"] * 2,
                "qc_level": [None, "lloq", "uloq"] * 2,
                "interferent": ["X", "X", "X", None, None, None],
                "signal": [2, 100, 200, None, 95, 205],
            }
        )
        calib_df = pd.DataFrame(
            {
                "concentration": [1, 1, 2, 2, 5],
                "signal": [20, 20, 50, 52, 100],
            }
        )
        ctx = self.make_ctx(df, calib_df)
        spec = SpecificitySpec()

        mocker.patch(
            (
                "yassa_bio"
                ".evaluation"
                ".acceptance"
                ".engine"
                ".specificity"
                ".compute_interferent_accuracy"
            ),
            return_value=None,
        )

        result = eval_specificity(ctx, spec)

        assert not result["lloq_accuracy"]["pass"]
        assert not result["uloq_accuracy"]["pass"]
        assert "error" in result["lloq_accuracy"]
        assert "error" in result["uloq_accuracy"]
        assert not result["pass"]
