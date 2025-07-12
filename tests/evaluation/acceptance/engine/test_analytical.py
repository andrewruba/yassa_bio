import pandas as pd

from yassa_bio.evaluation.acceptance.engine.analytical import eval_calibration
from yassa_bio.schema.acceptance.analytical import AnalyticalCalibrationSpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.enum import SampleType


def make_ctx(concs, signals, back_calc_fn) -> LBAContext:
    df = pd.DataFrame(
        {
            "concentration": concs,
            "signal": signals,
            "x": concs,
            "y": signals,
            "sample_type": SampleType.CALIBRATION_STANDARD.value,
        }
    )

    class DummyContext(LBAContext):
        calib_df = df
        curve_back = staticmethod(back_calc_fn)

    return DummyContext()


class TestEvalCalibration:
    def test_all_levels_pass(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[1, 2, 3, 4, 5, 6],
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
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec(min_levels=6)

        out = eval_calibration(ctx, spec)
        assert out["num_levels"] == 5
        assert out["pass"] is False
