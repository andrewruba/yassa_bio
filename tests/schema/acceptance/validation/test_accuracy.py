import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.accuracy import AccuracySpec


class TestAccuracySpec:
    def test_valid_instantiation_defaults(self):
        spec = AccuracySpec()
        assert spec.min_levels == 5
        assert spec.min_replicates_per_level == 3
        assert spec.acc_tol_pct_mid == 20
        assert spec.acc_tol_pct_edge == 25
        assert spec.total_error_pct_mid == 30
        assert spec.total_error_pct_edge == 40

    def test_valid_override_values(self):
        spec = AccuracySpec(
            min_levels=6,
            min_replicates_per_level=4,
            acc_tol_pct_mid=15,
            acc_tol_pct_edge=20,
            total_error_pct_mid=25,
            total_error_pct_edge=35,
        )
        assert spec.min_levels == 6
        assert spec.min_replicates_per_level == 4
        assert spec.acc_tol_pct_mid == 15
        assert spec.total_error_pct_edge == 35

    def test_invalid_low_min_levels(self):
        with pytest.raises(ValidationError) as e:
            AccuracySpec(min_levels=2)
        assert "min_levels" in str(e.value)

    def test_invalid_negative_percent(self):
        with pytest.raises(ValidationError) as e:
            AccuracySpec(acc_tol_pct_mid=-10)
        assert "acc_tol_pct_mid" in str(e.value)

    def test_invalid_percent_above_100(self):
        with pytest.raises(ValidationError) as e:
            AccuracySpec(total_error_pct_mid=150)
        assert "total_error_pct_mid" in str(e.value)

    def test_invalid_min_replicates(self):
        with pytest.raises(ValidationError) as e:
            AccuracySpec(min_replicates_per_level=0)
        assert "min_replicates_per_level" in str(e.value)
