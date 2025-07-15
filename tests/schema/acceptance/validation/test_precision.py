import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.precision import PrecisionSpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestPrecisionSpec:
    def test_valid_instantiation_defaults(self):
        spec = PrecisionSpec()
        assert spec.min_levels == 5
        assert spec.min_replicates_per_level == 3
        assert spec.cv_tol_pct_mid == 20
        assert spec.cv_tol_pct_edge == 25
        assert spec.total_error_pct_mid == 30
        assert spec.total_error_pct_edge == 40

    def test_required_well_patterns_defaults(self):
        spec = PrecisionSpec()
        assert len(spec.required_well_patterns) == 5
        expected_levels = {
            QCLevel.LLOQ,
            QCLevel.LOW,
            QCLevel.MID,
            QCLevel.HIGH,
            QCLevel.ULOQ,
        }
        actual_levels = {p.qc_level for p in spec.required_well_patterns}
        assert all(
            p.sample_type == SampleType.QUALITY_CONTROL
            for p in spec.required_well_patterns
        )
        assert actual_levels == expected_levels

    def test_valid_override_values(self):
        spec = PrecisionSpec(
            min_levels=6,
            min_replicates_per_level=4,
            cv_tol_pct_mid=10,
            cv_tol_pct_edge=15,
            total_error_pct_mid=20,
            total_error_pct_edge=25,
        )
        assert spec.min_levels == 6
        assert spec.min_replicates_per_level == 4
        assert spec.cv_tol_pct_mid == 10
        assert spec.total_error_pct_edge == 25

    def test_invalid_min_levels_too_low(self):
        with pytest.raises(ValidationError) as e:
            PrecisionSpec(min_levels=2)
        assert "min_levels" in str(e.value)

    def test_invalid_min_replicates_zero(self):
        with pytest.raises(ValidationError) as e:
            PrecisionSpec(min_replicates_per_level=0)
        assert "min_replicates_per_level" in str(e.value)

    def test_invalid_cv_tol_pct_mid_negative(self):
        with pytest.raises(ValidationError) as e:
            PrecisionSpec(cv_tol_pct_mid=-5)
        assert "cv_tol_pct_mid" in str(e.value)

    def test_invalid_total_error_pct_edge_above_100(self):
        with pytest.raises(ValidationError) as e:
            PrecisionSpec(total_error_pct_edge=120)
        assert "total_error_pct_edge" in str(e.value)
