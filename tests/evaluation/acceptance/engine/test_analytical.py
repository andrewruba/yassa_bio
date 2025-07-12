import pandas as pd

from yassa_bio.evaluation.acceptance.engine.analytical import eval_calibration, eval_qc
from yassa_bio.schema.acceptance.analytical import AnalyticalCalibrationSpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.analytical import AnalyticalQCSpec


def make_ctx(
    *,
    concs,
    signals,
    sample_type: SampleType,
    qc_levels=None,
    back_calc_fn,
) -> LBAContext:
    df = pd.DataFrame(
        {
            "concentration": concs,
            "signal": signals,
            "x": concs,
            "y": signals,
            "sample_type": sample_type.value,
            "qc_level": None,
        }
    )

    if qc_levels:
        df["qc_level"] = [lvl.value for lvl in qc_levels]

    class DummyContext:
        curve_back = staticmethod(back_calc_fn)
        calib_df = df
        data = df

    return DummyContext()


class TestEvalCalibration:
    def test_all_levels_pass(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[1, 2, 3, 4, 5, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,  # perfect match
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is True
        assert out["num_pass"] == out["num_levels"]
        assert out["can_refit"] is True
        assert out["failing_levels"] == []

    def test_one_edge_fails_but_can_refit(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6, 7],
            signals=[1.1, 2, 3, 4, 5, 6, 100],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert 7 in out["failing_levels"]
        assert out["can_refit"] is True

    def test_too_many_levels_fail(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[100, 100, 3, 4, 5, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert set(out["failing_levels"]) >= {1, 2}
        assert out["can_refit"] is False

    def test_not_enough_retained_levels(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[100, 2, 3, 4, 100, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec(min_retained_levels=5)

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert out["can_refit"] is False

    def test_too_few_levels_total(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5],
            signals=[1, 2, 3, 4, 5],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec(min_levels=6)

        out = eval_calibration(ctx, spec)
        assert out["num_levels"] == 5
        assert out["pass"] is False


class TestEvalQC:
    def test_all_levels_present_and_pass(self):
        ctx = make_ctx(
            concs=[10, 20, 30, 10, 20, 30],
            signals=[10, 20, 30, 10, 20, 30],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH] * 2,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is True
        assert out["num_pass"] == 6
        assert out["total_wells"] == 6
        for lvl in ("low", "mid", "high"):
            assert out["per_level"][lvl]["meets_level_fraction"]

    def test_missing_pattern_fails(self):
        ctx = make_ctx(
            concs=[10, 20],
            signals=[10, 20],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert "missing_patterns" in out
        assert out["error"].startswith("Missing")

    def test_bias_threshold_violation(self):
        ctx = make_ctx(
            concs=[10, 20, 30],
            signals=[20, 40, 60],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(qc_tol_pct=50)  # Will fail all (bias is 100%)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 0
        for v in out["per_level"].values():
            assert not v["meets_level_fraction"]

    def test_partial_level_failure(self):
        ctx = make_ctx(
            concs=[10, 20, 30, 10, 20, 30],
            signals=[10, 20, 30, 100, 20, 30],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH] * 2,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(pass_fraction_each_level=0.75)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 5
        assert out["per_level"]["low"]["num_pass"] == 1
        assert out["per_level"]["low"]["meets_level_fraction"] is False

    def test_fraction_total_fails(self):
        ctx = make_ctx(
            concs=[10, 20, 30],
            signals=[10, 200, 300],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(pass_fraction_total=0.8)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 1
        assert out["pass_fraction"] < 0.8

    def test_handles_no_qc_rows(self):
        ctx = make_ctx(
            concs=[],
            signals=[],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["error"] is not None

    def test_qc_level_with_zero_count(self):
        ctx = make_ctx(
            concs=[10, 20],
            signals=[10, 20],
            sample_type=SampleType.QUALITY_CONTROL,
            qc_levels=[QCLevel.LOW, QCLevel.MID],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["error"] is not None
