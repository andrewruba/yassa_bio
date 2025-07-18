import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.acceptance.validation.specificity import SpecificitySpec
from yassa_bio.schema.acceptance.validation.selectivity import SelectivitySpec
from yassa_bio.schema.acceptance.validation.calibration import CalibrationSpec
from yassa_bio.schema.acceptance.validation.accuracy import AccuracySpec
from yassa_bio.schema.acceptance.validation.precision import PrecisionSpec
from yassa_bio.schema.acceptance.validation.carryover import CarryoverSpec
from yassa_bio.schema.acceptance.validation.dilution import DilutionLinearitySpec
from yassa_bio.schema.acceptance.validation.stability import StabilitySpec
from yassa_bio.schema.acceptance.validation.parallelism import ParallelismSpec
from yassa_bio.schema.acceptance.validation.recovery import RecoverySpec
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


class TestLBAValidationAcceptanceCriteria:
    def test_defaults(self):
        criteria = LBAValidationAcceptanceCriteria()
        assert isinstance(criteria.specificity, SpecificitySpec)
        assert isinstance(criteria.selectivity, SelectivitySpec)
        assert isinstance(criteria.calibration, CalibrationSpec)
        assert isinstance(criteria.accuracy, AccuracySpec)
        assert isinstance(criteria.precision, PrecisionSpec)
        assert isinstance(criteria.carryover, CarryoverSpec)
        assert isinstance(criteria.dilution_linearity, DilutionLinearitySpec)
        assert isinstance(criteria.stability, StabilitySpec)
        assert isinstance(criteria.parallelism, ParallelismSpec)
        assert isinstance(criteria.recovery, RecoverySpec)

    def test_override_some_specs(self):
        custom = LBAValidationAcceptanceCriteria(
            accuracy=AccuracySpec(
                acc_tol_pct_mid=15,
                total_error_pct_mid=25,
            ),
            calibration=CalibrationSpec(
                pass_fraction=0.9,
            ),
            carryover=CarryoverSpec(
                min_blanks_after_uloq=2,
            ),
        )
        assert custom.accuracy.acc_tol_pct_mid == 15
        assert custom.calibration.pass_fraction == 0.9
        assert custom.carryover.min_blanks_after_uloq == 2

    def test_invalid_nested_model_raises(self):
        with pytest.raises(ValidationError) as e:
            LBAValidationAcceptanceCriteria(precision=PrecisionSpec(cv_tol_pct_mid=-5))
        assert "cv_tol_pct_mid" in str(e.value)

    def test_invalid_enum_in_nested_pattern(self):
        with pytest.raises(ValidationError) as e:
            LBAValidationAcceptanceCriteria(
                specificity=SpecificitySpec(
                    required_well_patterns=[
                        RequiredWellPattern(sample_type="not_a_type")
                    ]
                )
            )
        assert "sample_type" in str(e.value)

    def test_full_custom_instantiation_valid(self):
        full = LBAValidationAcceptanceCriteria(
            specificity=SpecificitySpec(acc_tol_pct=15),
            selectivity=SelectivitySpec(min_sources=5, pass_fraction=0.9),
            calibration=CalibrationSpec(pass_fraction=0.8),
            accuracy=AccuracySpec(acc_tol_pct_mid=10, total_error_pct_mid=15),
            precision=PrecisionSpec(cv_tol_pct_mid=15, total_error_pct_edge=20),
            carryover=CarryoverSpec(pass_fraction=0.9),
            dilution_linearity=DilutionLinearitySpec(
                pass_fraction=0.9, undiluted_recovery_min_pct=85
            ),
            stability=StabilitySpec(min_conditions=1, acc_tol_pct=30),
            parallelism=ParallelismSpec(pass_fraction=0.95),
            recovery=RecoverySpec(max_cv_pct_within_level=10),
        )
        assert full.precision.cv_tol_pct_mid == 15
        assert full.recovery.max_cv_pct_within_level == 10
        assert full.stability.acc_tol_pct == 30
