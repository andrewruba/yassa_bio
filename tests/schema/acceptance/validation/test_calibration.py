import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.calibration import CalibrationSpec


class TestCalibrationSpec:
    def test_valid_instantiation_defaults(self):
        spec = CalibrationSpec()
        assert spec.min_levels == 6
        assert spec.pass_fraction == 0.75
        assert spec.acc_tol_pct_mid == 20
        assert spec.acc_tol_pct_edge == 25
        assert spec.cv_tol_pct_mid == 20
        assert spec.cv_tol_pct_edge == 25

    def test_valid_override_values(self):
        spec = CalibrationSpec(
            min_levels=8,
            pass_fraction=0.85,
            acc_tol_pct_mid=15,
            acc_tol_pct_edge=20,
            cv_tol_pct_mid=10,
            cv_tol_pct_edge=15,
        )
        assert spec.min_levels == 8
        assert spec.pass_fraction == 0.85
        assert spec.acc_tol_pct_mid == 15
        assert spec.acc_tol_pct_edge == 20
        assert spec.cv_tol_pct_mid == 10
        assert spec.cv_tol_pct_edge == 15

    def test_rejects_invalid_pass_fraction(self):
        with pytest.raises(ValidationError) as e:
            CalibrationSpec(pass_fraction=1.2)
        assert "pass_fraction" in str(e.value)

    def test_rejects_negative_accuracy_tolerance(self):
        with pytest.raises(ValidationError) as e:
            CalibrationSpec(acc_tol_pct_mid=-5)
        assert "acc_tol_pct_mid" in str(e.value)

    def test_rejects_zero_min_levels(self):
        with pytest.raises(ValidationError) as e:
            CalibrationSpec(min_levels=0)
        assert "min_levels" in str(e.value)

    def test_rejects_precision_over_100(self):
        with pytest.raises(ValidationError) as e:
            CalibrationSpec(cv_tol_pct_mid=150)
        assert "cv_tol_pct_mid" in str(e.value)
