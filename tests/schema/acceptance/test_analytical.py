import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.analytical import (
    LBAAnalyticalAcceptanceCriteria,
    AnalyticalCalibrationSpec,
    AnalyticalQCSpec,
)
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestLBAAnalyticalAcceptanceValidation:
    def test_default_instantiation(self):
        criteria = LBAAnalyticalAcceptanceCriteria()

        cal = criteria.calibration
        assert isinstance(cal, AnalyticalCalibrationSpec)
        assert cal.min_levels == 6
        assert 0.0 < cal.pass_fraction <= 1.0
        assert cal.min_retained_levels >= 3

        qc = criteria.qc
        assert isinstance(qc, AnalyticalQCSpec)
        assert len(qc.required_well_patterns) == 3
        for pattern in qc.required_well_patterns:
            assert isinstance(pattern, RequiredWellPattern)
            assert pattern.sample_type == SampleType.QUALITY_CONTROL
            assert pattern.qc_level in {QCLevel.LOW, QCLevel.MID, QCLevel.HIGH}

        assert 0 < qc.qc_tol_pct < 100
        assert 0 < qc.pass_fraction_total <= 1.0
        assert 0 < qc.pass_fraction_each_level <= 1.0

    def test_override_values(self):
        new_cal = AnalyticalCalibrationSpec(
            min_levels=8,
            pass_fraction=0.9,
            acc_tol_pct_mid=15,
            acc_tol_pct_edge=20,
            min_retained_levels=5,
        )
        new_qc = AnalyticalQCSpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
                )
            ],
            qc_tol_pct=10,
            pass_fraction_total=0.9,
            pass_fraction_each_level=0.8,
        )
        criteria = LBAAnalyticalAcceptanceCriteria(
            calibration=new_cal,
            qc=new_qc,
        )

        assert criteria.calibration.min_levels == 8
        assert criteria.qc.qc_tol_pct == 10
        assert len(criteria.qc.required_well_patterns) == 1

    def test_reject_invalid_percent(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalCalibrationSpec(
                min_levels=6,
                pass_fraction=1.5,
                acc_tol_pct_mid=20,
                acc_tol_pct_edge=25,
                min_retained_levels=6,
            )
        assert "pass_fraction" in str(e.value)

    def test_reject_negative_tol(self):
        with pytest.raises(ValidationError) as e:
            AnalyticalQCSpec(
                required_well_patterns=[
                    RequiredWellPattern(
                        sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
                    )
                ],
                qc_tol_pct=-5,  # invalid
                pass_fraction_total=0.5,
                pass_fraction_each_level=0.5,
            )
        assert "qc_tol_pct" in str(e.value)
