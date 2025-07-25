import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.dilution import (
    ValidationDilutionLinearitySpec,
)
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestValidationDilutionLinearitySpec:
    def test_default_instantiation(self):
        spec = ValidationDilutionLinearitySpec()
        assert spec.min_dilutions >= 0
        assert spec.min_replicates >= 1
        assert 0 < spec.acc_tol_pct <= 100
        assert 0 < spec.cv_tol_pct <= 100
        assert 0 < spec.undiluted_recovery_min_pct <= 100

        assert len(spec.required_well_patterns) == 1
        p = spec.required_well_patterns[0]
        assert p.sample_type == SampleType.QUALITY_CONTROL
        assert p.qc_level == QCLevel.ABOVE_ULOQ

    def test_custom_instantiation(self):
        spec = ValidationDilutionLinearitySpec(
            min_dilutions=5,
            min_replicates=4,
            acc_tol_pct=15,
            cv_tol_pct=10,
            undiluted_recovery_min_pct=85,
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL,
                    qc_level=QCLevel.ABOVE_ULOQ,
                )
            ],
        )
        assert spec.min_dilutions == 5
        assert spec.min_replicates == 4
        assert spec.acc_tol_pct == 15
        assert spec.undiluted_recovery_min_pct == 85

    def test_reject_acc_tol_pct_above_100(self):
        with pytest.raises(ValidationError) as e:
            ValidationDilutionLinearitySpec(acc_tol_pct=150)
        assert "acc_tol_pct" in str(e.value)

    def test_reject_cv_tol_pct_above_100(self):
        with pytest.raises(ValidationError) as e:
            ValidationDilutionLinearitySpec(cv_tol_pct=101)
        assert "cv_tol_pct" in str(e.value)

    def test_reject_undiluted_recovery_above_100(self):
        with pytest.raises(ValidationError) as e:
            ValidationDilutionLinearitySpec(undiluted_recovery_min_pct=101)
        assert "undiluted_recovery_min_pct" in str(e.value)

    def test_reject_min_replicates_below_1(self):
        with pytest.raises(ValidationError) as e:
            ValidationDilutionLinearitySpec(min_replicates=0)
        assert "min_replicates" in str(e.value)

    def test_reject_min_dilutions_below_0(self):
        with pytest.raises(ValidationError) as e:
            ValidationDilutionLinearitySpec(min_dilutions=-1)
        assert "min_dilutions" in str(e.value)
