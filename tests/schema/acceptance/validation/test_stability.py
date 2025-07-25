import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.stability import ValidationStabilitySpec
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestValidationStabilitySpec:
    def test_valid_instantiation(self):
        spec = ValidationStabilitySpec()
        assert 0 <= spec.min_conditions
        assert 0 < spec.acc_tol_pct <= 100

        patterns = spec.required_well_patterns
        assert len(patterns) == 2
        for p in patterns:
            assert p.sample_type == SampleType.QUALITY_CONTROL
            assert p.needs_stability_condition is True
            assert p.qc_level in {QCLevel.LOW, QCLevel.HIGH}

    def test_override_fields(self):
        spec = ValidationStabilitySpec(
            min_conditions=2,
            acc_tol_pct=15,
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL,
                    qc_level=QCLevel.MID,
                    needs_stability_condition=True,
                )
            ],
        )
        assert spec.min_conditions == 2
        assert spec.acc_tol_pct == 15
        assert len(spec.required_well_patterns) == 1
        assert spec.required_well_patterns[0].qc_level == QCLevel.MID

    def test_reject_invalid_percent(self):
        with pytest.raises(ValidationError) as e:
            ValidationStabilitySpec(acc_tol_pct=120)
        assert "acc_tol_pct" in str(e.value)

    def test_reject_negative_min_conditions(self):
        with pytest.raises(ValidationError) as e:
            ValidationStabilitySpec(min_conditions=-1)
        assert "min_conditions" in str(e.value)
