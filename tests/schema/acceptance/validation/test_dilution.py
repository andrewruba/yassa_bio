import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.dilution import DilutionLinearitySpec


class TestDilutionLinearitySpec:
    def test_default_instantiation(self):
        spec = DilutionLinearitySpec()
        assert spec.min_dilution_factors >= 0
        assert spec.min_series >= 1
        assert spec.min_replicates_per_point >= 1
        assert 0 < spec.pass_fraction <= 1.0
        assert 0 < spec.bias_tol_pct <= 100
        assert 0 < spec.cv_tol_pct <= 100
        assert 0 < spec.hook_check_threshold_pct <= 100

    def test_custom_instantiation(self):
        spec = DilutionLinearitySpec(
            min_dilution_factors=5,
            min_series=4,
            min_replicates_per_point=2,
            pass_fraction=0.8,
            bias_tol_pct=15,
            cv_tol_pct=10,
            hook_check_threshold_pct=85,
        )
        assert spec.min_dilution_factors == 5
        assert spec.min_series == 4
        assert spec.pass_fraction == 0.8
        assert spec.hook_check_threshold_pct == 85

    def test_reject_pass_fraction_above_one(self):
        with pytest.raises(ValidationError) as e:
            DilutionLinearitySpec(pass_fraction=1.2)
        assert "pass_fraction" in str(e.value)

    def test_reject_bias_tol_pct_above_100(self):
        with pytest.raises(ValidationError) as e:
            DilutionLinearitySpec(bias_tol_pct=150)
        assert "bias_tol_pct" in str(e.value)

    def test_reject_hook_threshold_above_100(self):
        with pytest.raises(ValidationError) as e:
            DilutionLinearitySpec(hook_check_threshold_pct=101)
        assert "hook_check_threshold_pct" in str(e.value)

    def test_reject_min_series_below_one(self):
        with pytest.raises(ValidationError) as e:
            DilutionLinearitySpec(min_series=0)
        assert "min_series" in str(e.value)
