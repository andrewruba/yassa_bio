import numpy as np
import pytest

from yassa_bio.evaluation.analysis.engine.weighting import (
    weight_one,
    weight_one_over_x,
    weight_one_over_x2,
    weight_one_over_y,
    weight_one_over_y2,
)


class TestWeighting:
    @pytest.fixture(scope="class")
    def xy(self):
        x = np.array([0.0, 1.0, 2.0, 4.0])
        y = np.array([0.0, 2.0, 4.0, 8.0])
        return x, y

    @pytest.mark.parametrize(
        "fn, expected",
        [
            (weight_one, np.array([1.0, 1.0, 1.0, 1.0])),
            (weight_one_over_x, np.array([np.inf, 1.0, 0.5, 0.25])),
            (weight_one_over_x2, np.array([np.inf, 1.0, 0.25, 0.0625])),
            (weight_one_over_y, np.array([np.inf, 0.5, 0.25, 0.125])),
            (weight_one_over_y2, np.array([np.inf, 0.25, 0.0625, 0.015625])),
        ],
    )
    def test_weights(self, xy, fn, expected):
        x, y = xy

        with np.errstate(divide="ignore", invalid="ignore"):
            w = fn(x, y)

        assert w.shape == x.shape
        assert np.allclose(w, expected, equal_nan=True)
