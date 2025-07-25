import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.recovery import ValidationRecoverySpec
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage


class TestValidationRecoverySpec:
    def test_default_instantiation(self):
        spec = ValidationRecoverySpec()

        patterns = {(p.qc_level, p.recovery_stage) for p in spec.required_well_patterns}
        expected = {
            (QCLevel.LOW, RecoveryStage.BEFORE),
            (QCLevel.MID, RecoveryStage.BEFORE),
            (QCLevel.HIGH, RecoveryStage.BEFORE),
            (QCLevel.LOW, RecoveryStage.AFTER),
            (QCLevel.MID, RecoveryStage.AFTER),
            (QCLevel.HIGH, RecoveryStage.AFTER),
        }
        assert patterns == expected

        assert 0 < spec.max_cv_pct_within_level <= 100
        assert 0 < spec.max_diff_pct_between_levels <= 100
        assert spec.min_replicates_each >= 1

    def test_custom_instantiation(self):
        spec = ValidationRecoverySpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL,
                    qc_level=QCLevel.LOW,
                    recovery_stage=RecoveryStage.AFTER,
                )
            ],
            min_replicates_each=5,
            max_cv_pct_within_level=10,
            max_diff_pct_between_levels=12,
        )
        assert len(spec.required_well_patterns) == 1
        assert spec.min_replicates_each == 5
        assert spec.max_cv_pct_within_level == 10
        assert spec.max_diff_pct_between_levels == 12

    def test_invalid_min_replicates_each(self):
        with pytest.raises(ValidationError) as e:
            ValidationRecoverySpec(min_replicates_each=0)
        assert "min_replicates_each" in str(e.value)

    def test_invalid_cv_within_level(self):
        with pytest.raises(ValidationError) as e:
            ValidationRecoverySpec(max_cv_pct_within_level=150)
        assert "max_cv_pct_within_level" in str(e.value)

    def test_invalid_diff_between_levels(self):
        with pytest.raises(ValidationError) as e:
            ValidationRecoverySpec(max_diff_pct_between_levels=999)
        assert "max_diff_pct_between_levels" in str(e.value)
