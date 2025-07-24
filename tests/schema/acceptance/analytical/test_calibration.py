import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.analytical.calibration import AnalyticalCalibrationSpec


class TestAnalyticalCalibrationSpec:
    def test_valid_instantiation_defaults(self):
        spec = AnalyticalCalibrationSpec()
        assert spec.min_levels == 6
        assert spec.pass_fraction == 0.75
        assert spec.acc_tol_pct_mid == 20
        assert spec.acc_tol_pct_edge == 25
        assert spec.min_retained_levels == 6

    def test_valid_override_values(self):
        spec = AnalyticalCalibrationSpec(
            min_levels=6,
            pass_fraction=0.9,
            acc_tol_pct_mid=15,
            acc_tol_pct_edge=20,
            min_retained_levels=5,
        )
        assert spec.pass_fraction == 0.9
        assert spec.acc_tol_pct_mid == 15
        assert spec.acc_tol_pct_edge == 20
        assert spec.min_retained_levels == 5

    def test_invalid_min_levels_below_6(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(min_levels=5)
        assert "min_levels" in str(e.value)

    def test_invalid_negative_percent(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(acc_tol_pct_mid=-10)
        assert "acc_tol_pct_mid" in str(e.value)

    def test_invalid_percent_above_100(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(acc_tol_pct_edge=120)
        assert "acc_tol_pct_edge" in str(e.value)

    def test_invalid_fraction_above_one(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(pass_fraction=1.5)
        assert "pass_fraction" in str(e.value)

    def test_invalid_min_retained_levels_below_3(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(min_retained_levels=2)
        assert "min_retained_levels" in str(e.value)
