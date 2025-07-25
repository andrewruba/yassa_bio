import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.specificity import ValidationSpecificitySpec
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestValidationSpecificitySpec:
    def test_valid_instantiation(self):
        spec = ValidationSpecificitySpec()

        assert 0.0 < spec.acc_tol_pct <= 100

        patterns = spec.required_well_patterns
        assert len(patterns) == 3
        assert all(p.needs_interferent for p in patterns)

        assert any(p.sample_type == SampleType.BLANK for p in patterns)
        assert any(
            p.sample_type == SampleType.QUALITY_CONTROL and p.qc_level == QCLevel.LLOQ
            for p in patterns
        )
        assert any(
            p.sample_type == SampleType.QUALITY_CONTROL and p.qc_level == QCLevel.ULOQ
            for p in patterns
        )

    def test_override_values(self):
        custom_spec = ValidationSpecificitySpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.BLANK, needs_interferent=True
                )
            ],
            acc_tol_pct=15,
        )

        assert custom_spec.acc_tol_pct == 15
        assert len(custom_spec.required_well_patterns) == 1
        assert custom_spec.required_well_patterns[0].sample_type == SampleType.BLANK

    def test_reject_negative_percent(self):
        with pytest.raises(ValidationError) as e:
            ValidationSpecificitySpec(acc_tol_pct=-5)
        assert "acc_tol_pct" in str(e.value)
