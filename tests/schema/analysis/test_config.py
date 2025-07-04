import pytest
from pydantic import ValidationError

from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.analysis.preprocessing import (
    Preprocessing,
    OutlierParams,
)
from yassa_bio.schema.analysis.fit import CurveFit
from yassa_bio.schema.analysis.enum import (
    OutlierRule,
    CurveModel,
    Weighting,
    Transformation,
)


class TestLBAAnalysisConfig:
    def test_defaults_round_trip(self):
        cfg = LBAAnalysisConfig()

        assert cfg.preprocessing.blank_subtract is True
        assert cfg.preprocessing.normalize_to_control is False
        assert cfg.preprocessing.outliers.rule is OutlierRule.NONE

        assert cfg.curve_fit.model is CurveModel.FOUR_PL
        assert cfg.curve_fit.weighting is Weighting.ONE
        assert cfg.curve_fit.transformation_x is Transformation.IDENTITY
        assert cfg.curve_fit.transformation_y is Transformation.IDENTITY

    def test_custom_nested_objects(self):
        custom_pre = Preprocessing(
            blank_subtract=False,
            normalize_to_control=True,
            outliers=OutlierParams(rule="iqr", iqr_k=2.5),
        )
        custom_fit = CurveFit(
            model="linear",
            transformation_x="log2",
            transformation_y="sqrt",
            weighting="1/x",
        )

        cfg = LBAAnalysisConfig(preprocessing=custom_pre, curve_fit=custom_fit)

        assert cfg.preprocessing == custom_pre
        assert cfg.curve_fit == custom_fit

    def test_invalid_nested_preprocessing_raises(self):
        bad_outliers = {"rule": "zscore", "z_threshold": None}
        with pytest.raises(ValidationError):
            LBAAnalysisConfig(preprocessing={"outliers": bad_outliers})

    def test_invalid_nested_curvefit_raises(self):
        bad_fit = {"model": "7PL"}
        with pytest.raises(ValidationError):
            LBAAnalysisConfig(curve_fit=bad_fit)
