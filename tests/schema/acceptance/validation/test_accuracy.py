import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.accuracy import ValidationAccuracySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestValidationAccuracySpec:
    def test_valid_instantiation_defaults(self):
        spec = ValidationAccuracySpec()
        assert spec.min_levels == 5
        assert spec.min_replicates_per_level == 3
        assert spec.acc_tol_pct_mid == 20
        assert spec.acc_tol_pct_edge == 25
        assert spec.total_error_pct_mid == 30
        assert spec.total_error_pct_edge == 40

    def test_default_required_well_patterns_present_and_valid(self):
        spec = ValidationAccuracySpec()
        patterns = spec.required_well_patterns
        assert isinstance(patterns, list)
        assert len(patterns) == 5

        expected_qc_levels = {
            QCLevel.LLOQ,
            QCLevel.LOW,
            QCLevel.MID,
            QCLevel.HIGH,
            QCLevel.ULOQ,
        }

        seen_qc_levels = {p.qc_level for p in patterns}
        assert seen_qc_levels == expected_qc_levels
        for p in patterns:
            assert p.sample_type == SampleType.QUALITY_CONTROL

    def test_valid_override_values(self):
        spec = ValidationAccuracySpec(
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
            ValidationAccuracySpec(min_levels=0)
        assert "min_levels" in str(e.value)

    def test_invalid_negative_percent(self):
        with pytest.raises(ValidationError) as e:
            ValidationAccuracySpec(acc_tol_pct_mid=-10)
        assert "acc_tol_pct_mid" in str(e.value)

    def test_invalid_percent_above_100(self):
        with pytest.raises(ValidationError) as e:
            ValidationAccuracySpec(total_error_pct_mid=150)
        assert "total_error_pct_mid" in str(e.value)

    def test_invalid_min_replicates(self):
        with pytest.raises(ValidationError) as e:
            ValidationAccuracySpec(min_replicates_per_level=0)
        assert "min_replicates_per_level" in str(e.value)
