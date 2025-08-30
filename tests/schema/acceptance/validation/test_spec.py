import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.acceptance.validation.specificity import ValidationSpecificitySpec
from yassa_bio.schema.acceptance.validation.selectivity import ValidationSelectivitySpec
from yassa_bio.schema.acceptance.validation.calibration import ValidationCalibrationSpec
from yassa_bio.schema.acceptance.validation.accuracy import ValidationAccuracySpec
from yassa_bio.schema.acceptance.validation.precision import ValidationPrecisionSpec
from yassa_bio.schema.acceptance.validation.carryover import ValidationCarryoverSpec
from yassa_bio.schema.acceptance.validation.dilution import (
    ValidationDilutionLinearitySpec,
)
from yassa_bio.schema.acceptance.validation.stability import ValidationStabilitySpec
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern


class TestLBAValidationAcceptanceCriteria:
    def test_defaults(self):
        criteria = LBAValidationAcceptanceCriteria()
        assert isinstance(criteria.specificity, ValidationSpecificitySpec)
        assert isinstance(criteria.selectivity, ValidationSelectivitySpec)
        assert isinstance(criteria.calibration, ValidationCalibrationSpec)
        assert isinstance(criteria.accuracy, ValidationAccuracySpec)
        assert isinstance(criteria.precision, ValidationPrecisionSpec)
        assert isinstance(criteria.carryover, ValidationCarryoverSpec)
        assert isinstance(criteria.dilution_linearity, ValidationDilutionLinearitySpec)
        assert isinstance(criteria.stability, ValidationStabilitySpec)

    def test_override_some_specs(self):
        custom = LBAValidationAcceptanceCriteria(
            accuracy=ValidationAccuracySpec(
                acc_tol_pct_mid=15,
                total_error_pct_mid=25,
            ),
            calibration=ValidationCalibrationSpec(
                pass_fraction=0.9,
            ),
            carryover=ValidationCarryoverSpec(
                min_blanks_after_uloq=2,
            ),
        )
        assert custom.accuracy.acc_tol_pct_mid == 15
        assert custom.calibration.pass_fraction == 0.9
        assert custom.carryover.min_blanks_after_uloq == 2

    def test_invalid_nested_model_raises(self):
        with pytest.raises(ValidationError) as e:
            LBAValidationAcceptanceCriteria(
                precision=ValidationPrecisionSpec(cv_tol_pct_mid=-5)
            )
        assert "cv_tol_pct_mid" in str(e.value)

    def test_invalid_enum_in_nested_pattern(self):
        with pytest.raises(ValidationError) as e:
            LBAValidationAcceptanceCriteria(
                specificity=ValidationSpecificitySpec(
                    required_well_patterns=[
                        RequiredWellPattern(sample_type="not_a_type")
                    ]
                )
            )
        assert "sample_type" in str(e.value)

    def test_full_custom_instantiation_valid(self):
        full = LBAValidationAcceptanceCriteria(
            specificity=ValidationSpecificitySpec(acc_tol_pct=15),
            selectivity=ValidationSelectivitySpec(min_sources=5, pass_fraction=0.9),
            calibration=ValidationCalibrationSpec(pass_fraction=0.8),
            accuracy=ValidationAccuracySpec(acc_tol_pct_mid=10, total_error_pct_mid=15),
            precision=ValidationPrecisionSpec(
                cv_tol_pct_mid=15, total_error_pct_edge=20
            ),
            carryover=ValidationCarryoverSpec(pass_fraction=0.9),
            dilution_linearity=ValidationDilutionLinearitySpec(
                pass_fraction=0.9, undiluted_recovery_min_pct=85
            ),
            stability=ValidationStabilitySpec(min_conditions=1, acc_tol_pct=30),
        )
        assert full.precision.cv_tol_pct_mid == 15
        assert full.stability.acc_tol_pct == 30
