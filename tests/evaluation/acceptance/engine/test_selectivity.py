import pandas as pd
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.validation.selectivity import SelectivitySpec
from yassa_bio.evaluation.acceptance.engine.selectivity import (
    eval_selectivity,
    evaluate_source_group,
)


class TestEvalSelectivity:
    def make_ctx(self, df: pd.DataFrame, calib_df: pd.DataFrame):
        class DummyCtx:
            def __init__(self, df, calib_df):
                self.data = df
                self.calib_df = calib_df
                self.curve_back = lambda y: y

        return DummyCtx(df, calib_df)

    def test_valid_pass_case(self):
        df = pd.DataFrame(
            {
                "matrix_source_id": ["A"] * 3,
                "matrix_type": ["cat"] * 3,
                "sample_type": [
                    SampleType.BLANK,
                    SampleType.QUALITY_CONTROL,
                    SampleType.QUALITY_CONTROL,
                ],
                "qc_level": [None, QCLevel.LLOQ, QCLevel.HIGH],
                "x": [None, 20, 100],
                "y": [2, 22, 105],
                "signal": [2, 22, 105],
            }
        )
        calib_df = pd.DataFrame({"concentration": [1], "signal": [20]})
        spec = SelectivitySpec(min_sources=1)
        ctx = self.make_ctx(df, calib_df)

        result = eval_selectivity(ctx, spec)

        assert result["pass"]
        assert result["num_sources"] == 1
        assert result["num_passed"] == 1
        assert result["matrix_types"] == {"cat": 1}

    def test_missing_required_patterns(self):
        df = pd.DataFrame(
            {
                "matrix_source_id": ["Z"],
                "matrix_type": ["mystery"],
                "sample_type": [SampleType.BLANK],
                "qc_level": [None],
                "signal": [5],
            }
        )
        calib_df = pd.DataFrame({"concentration": [1], "signal": [20]})
        spec = SelectivitySpec()
        ctx = self.make_ctx(df, calib_df)

        result = eval_selectivity(ctx, spec)

        assert "error" in result
        assert "missing_patterns" in result
        assert not result["pass"]

    def test_lloq_signal_none_fails_all(self):
        df = pd.DataFrame(
            {
                "matrix_source_id": ["X"] * 3,
                "matrix_type": ["bat"] * 3,
                "sample_type": [
                    SampleType.BLANK,
                    SampleType.QUALITY_CONTROL,
                    SampleType.QUALITY_CONTROL,
                ],
                "qc_level": [None, QCLevel.LLOQ, QCLevel.HIGH],
                "x": [None, 20, 100],
                "y": [5, 22, 105],
                "signal": [5, 22, 105],
            }
        )
        calib_df = pd.DataFrame(columns=["concentration", "signal"])
        spec = SelectivitySpec(min_sources=1)
        ctx = self.make_ctx(df, calib_df)

        result = eval_selectivity(ctx, spec)

        assert "error" in result
        assert not result["pass"]

    def test_fraction_pass_threshold(self):
        # Two sources: one passes, one fails
        df = pd.DataFrame(
            [
                # Source A (pass)
                ["A", "dog", SampleType.BLANK, None, None, 2, 2],
                ["A", "dog", SampleType.QUALITY_CONTROL, QCLevel.LLOQ, 20, 22, 22],
                ["A", "dog", SampleType.QUALITY_CONTROL, QCLevel.HIGH, 100, 105, 105],
                # Source B (fail)
                ["B", "dog", SampleType.BLANK, None, None, 2, 2],
                ["B", "dog", SampleType.QUALITY_CONTROL, QCLevel.LLOQ, 20, 80, 80],
                ["B", "dog", SampleType.QUALITY_CONTROL, QCLevel.HIGH, 100, 190, 190],
            ],
            columns=[
                "matrix_source_id",
                "matrix_type",
                "sample_type",
                "qc_level",
                "x",
                "y",
                "signal",
            ],
        )
        calib_df = pd.DataFrame({"concentration": [1], "signal": [20]})
        spec = SelectivitySpec(min_sources=2, pass_fraction=0.5)
        ctx = self.make_ctx(df, calib_df)

        result = eval_selectivity(ctx, spec)

        assert result["num_sources"] == 2
        assert result["num_passed"] == 1
        assert result["pass"]


class TestEvaluateSourceGroup:
    def test_all_checks_pass(self):
        df = pd.DataFrame(
            {
                "sample_type": [
                    SampleType.BLANK,
                    SampleType.QUALITY_CONTROL,
                    SampleType.QUALITY_CONTROL,
                ],
                "qc_level": [None, QCLevel.LLOQ, QCLevel.HIGH],
                "matrix_type": ["rat"] * 3,
                "x": [None, 20, 100],
                "y": [2, 22, 105],
                "signal": [2, 22, 105],
            }
        )
        lloq_signal = 20
        spec = SelectivitySpec()

        def back_calc(y):
            return y

        result = evaluate_source_group(
            df,
            matrix_type="rat",
            lloq_signal=lloq_signal,
            spec=spec,
            back_calc_fn=back_calc,
        )

        assert result["blank_ok"]
        assert result["lloq_ok"]
        assert result["high_ok"]
        assert result["pass"]

    def test_blank_above_lloq(self):
        df = pd.DataFrame(
            {
                "sample_type": [SampleType.BLANK],
                "qc_level": [None],
                "matrix_type": ["rat"],
                "x": [None],
                "y": [30],
                "signal": [30],
            }
        )
        lloq_signal = 20
        spec = SelectivitySpec()
        result = evaluate_source_group(
            df,
            matrix_type="rat",
            lloq_signal=lloq_signal,
            spec=spec,
            back_calc_fn=lambda y: y,
        )

        assert not result["blank_ok"]
        assert not result["pass"]

    def test_lloq_and_high_accuracy_fail(self):
        df = pd.DataFrame(
            {
                "sample_type": [SampleType.QUALITY_CONTROL, SampleType.QUALITY_CONTROL],
                "qc_level": [QCLevel.LLOQ, QCLevel.HIGH],
                "matrix_type": ["rat", "rat"],
                "x": [20, 100],
                "y": [80, 180],
                "signal": [80, 180],
            }
        )
        spec = SelectivitySpec()
        result = evaluate_source_group(
            df, matrix_type="rat", lloq_signal=20, spec=spec, back_calc_fn=lambda y: y
        )

        assert not result["lloq_ok"]
        assert not result["high_ok"]
        assert not result["pass"]

    def test_missing_qc_levels(self):
        df = pd.DataFrame(
            {
                "sample_type": [SampleType.BLANK],
                "qc_level": [None],
                "matrix_type": ["rat"],
                "x": [None],
                "y": [2],
                "signal": [2],
            }
        )
        spec = SelectivitySpec()
        result = evaluate_source_group(
            df, matrix_type="rat", lloq_signal=20, spec=spec, back_calc_fn=lambda y: y
        )

        assert result["blank_ok"]
        assert not result["lloq_ok"]
        assert not result["high_ok"]
        assert not result["pass"]
