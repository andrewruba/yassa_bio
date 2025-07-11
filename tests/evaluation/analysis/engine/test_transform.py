import numpy as np
import pytest

from yassa_bio.evaluation.analysis.engine.transform import (
    transform_identity,
    transform_ln,
    transform_log2,
    transform_log10,
    transform_sqrt,
    transform_reciprocal,
)


class TestTransforms:
    @pytest.mark.parametrize(
        "fn, expected",
        [
            (transform_identity, lambda x: x),
            (transform_ln, np.log),
            (transform_log2, np.log2),
            (transform_log10, np.log10),
            (transform_sqrt, np.sqrt),
            (transform_reciprocal, lambda x: 1 / x),
        ],
    )
    def test_basics(self, fn, expected):
        x = np.array([1.0, 4.0, 10.0])
        y = fn(x)
        np.testing.assert_allclose(y, expected(x), rtol=1e-12, atol=0)

    def test_reciprocal_handles_zero(self):
        x = np.array([0.0, 2.0])
        with np.errstate(divide="ignore"):
            y = transform_reciprocal(x)
        assert np.isinf(y[0])
        assert y[1] == 0.5

    def test_log_negative_gives_nan(self):
        x = np.array([-1.0, 1.0, 0.0])

        with np.errstate(divide="ignore", invalid="ignore"):
            out_ln = transform_ln(x)
            out_lg2 = transform_log2(x)
            out_lg10 = transform_log10(x)

        for out in (out_ln, out_lg2, out_lg10):
            assert np.isnan(out[0])
            assert np.isneginf(out[2])

    def test_sqrt_negative_gives_nan(self):
        x = np.array([-4.0, 4.0])
        with np.errstate(invalid="ignore"):
            y = transform_sqrt(x)
        assert np.isnan(y[0])
        assert y[1] == 2.0
