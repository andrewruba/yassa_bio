import numpy as np
import pytest

from yassa_bio.evaluation.analysis.engine.model import (
    fit_4pl,
    fit_5pl,
    fit_linear,
    back_4pl,
    back_5pl,
    back_linear,
    _4pl,
    _5pl,
    _linear,
)
from yassa_bio.schema.analysis.enum import CurveModel


rng = np.random.default_rng(42)


def _noisy(y, noise=0.02):
    """Add small proportional noise to y values."""
    return y * (1 + rng.normal(scale=noise, size=y.size))


SYNTH_PARAMS = {
    CurveModel.LINEAR: np.array([2.0, 5.0]),
    CurveModel.FOUR_PL: np.array([1.5, 1.2, 50.0, 0.1]),
    CurveModel.FIVE_PL: np.array([1.5, 1.2, 50.0, 0.1, 0.8]),
}

FIT_FUNCS = {
    CurveModel.LINEAR: fit_linear,
    CurveModel.FOUR_PL: fit_4pl,
    CurveModel.FIVE_PL: fit_5pl,
}

BACK_FUNCS = {
    CurveModel.LINEAR: back_linear,
    CurveModel.FOUR_PL: back_4pl,
    CurveModel.FIVE_PL: back_5pl,
}

FWD_FUNCS = {
    CurveModel.LINEAR: _linear,
    CurveModel.FOUR_PL: _4pl,
    CurveModel.FIVE_PL: _5pl,
}


class TestModel:
    @pytest.mark.parametrize(
        "model", [CurveModel.LINEAR, CurveModel.FOUR_PL, CurveModel.FIVE_PL]
    )
    def test_fit_and_backcalc_roundtrip(self, model):
        params_true = SYNTH_PARAMS[model]
        f_true = FWD_FUNCS[model]

        x = np.linspace(1, 100, 40)
        y = _noisy(f_true(x, *params_true))
        w = 1 / y

        f_fit, params_est = FIT_FUNCS[model](x, y, weights=w)

        y_pred = f_fit(x)
        assert np.allclose(y_pred, y, rtol=0.05, atol=0.05)

        x_back = BACK_FUNCS[model](y_pred, params_est)
        assert np.allclose(x_back, x, rtol=0.05, atol=0.05)

    def test_linear_two_point_exact(self):
        x = np.array([0.0, 10.0])
        y = 3.0 * x + 7.0  # y = 3x + 7

        f_fit, coef = fit_linear(x, y)
        m, b = coef

        assert pytest.approx(m, rel=1e-12) == 3.0
        assert pytest.approx(b, rel=1e-12) == 7.0
        assert np.allclose(f_fit(x), y)
