import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.analytical.qc import QCSpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestQCSpec:
    def test_valid_instantiation_defaults(self):
        spec = QCSpec()
        assert spec.acc_tol_pct == 20
        assert spec.pass_fraction_total == pytest.approx(2 / 3)
        assert spec.pass_fraction_each_level == 0.5

    def test_default_required_well_patterns_present_and_valid(self):
        spec = QCSpec()
        patterns = spec.required_well_patterns
        assert isinstance(patterns, list)
        assert len(patterns) == 3

        expected_qc_levels = {QCLevel.LOW, QCLevel.MID, QCLevel.HIGH}
        seen_qc_levels = {p.qc_level for p in patterns}
        assert seen_qc_levels == expected_qc_levels
        for p in patterns:
            assert p.sample_type == SampleType.QUALITY_CONTROL

    def test_valid_override_values(self):
        spec = QCSpec(
            acc_tol_pct=10,
            pass_fraction_total=0.75,
            pass_fraction_each_level=0.6,
        )
        assert spec.acc_tol_pct == 10
        assert spec.pass_fraction_total == 0.75
        assert spec.pass_fraction_each_level == 0.6

    def test_invalid_negative_percent(self):
        with pytest.raises(ValidationError) as e:
            QCSpec(acc_tol_pct=-10)
        assert "acc_tol_pct" in str(e.value)

    def test_invalid_percent_above_100(self):
        with pytest.raises(ValidationError) as e:
            QCSpec(acc_tol_pct=150)
        assert "acc_tol_pct" in str(e.value)

    def test_invalid_fraction_total_too_high(self):
        with pytest.raises(ValidationError) as e:
            QCSpec(pass_fraction_total=1.5)
        assert "pass_fraction_total" in str(e.value)

    def test_invalid_fraction_each_level_negative(self):
        with pytest.raises(ValidationError) as e:
            QCSpec(pass_fraction_each_level=-0.2)
        assert "pass_fraction_each_level" in str(e.value)
