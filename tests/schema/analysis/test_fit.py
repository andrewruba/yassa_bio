from pydantic import ValidationError
import pytest

from yassa_bio.schema.analysis.fit import CurveFit
from yassa_bio.schema.analysis.enum import (
    CurveModel,
    Weighting,
    Transformation,
)


class TestCurveFitDefaults:
    def test_defaults_round_trip(self) -> None:
        cf = CurveFit()
        assert cf.model is CurveModel.FOUR_PL
        assert cf.transformation_x is Transformation.IDENTITY
        assert cf.transformation_y is Transformation.IDENTITY
        assert cf.weighting is Weighting.ONE

    def test_non_default_valid(self) -> None:
        cf = CurveFit(
            model="5PL",
            transformation_x="log10",
            transformation_y="sqrt",
            weighting="1/x^2",
        )
        assert cf.model is CurveModel.FIVE_PL
        assert cf.transformation_x is Transformation.LOG10
        assert cf.transformation_y is Transformation.SQRT
        assert cf.weighting is Weighting.ONE_OVER_X2

    @pytest.mark.parametrize(
        "bad_model",
        ["7PL", "quad", "", None],
    )
    def test_invalid_model_raises(self, bad_model) -> None:
        with pytest.raises(ValidationError):
            CurveFit(model=bad_model)

    @pytest.mark.parametrize(
        "bad_weight",
        ["1/z", "random-weight", 123],
    )
    def test_invalid_weighting_raises(self, bad_weight) -> None:
        with pytest.raises(ValidationError):
            CurveFit(weighting=bad_weight)

    def test_dump_and_load(self) -> None:
        cfg = CurveFit(
            model="linear",
            transformation_x="log2",
            transformation_y="reciprocal",
            weighting="1/y",
        )
        blob = cfg.model_dump(mode="json")

        restored = CurveFit(**blob)
        assert restored == cfg
