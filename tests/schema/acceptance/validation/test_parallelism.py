import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.parallelism import ParallelismSpec
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType


class TestParallelismSpec:
    def test_valid_instantiation(self):
        spec = ParallelismSpec()
        assert spec.min_dilutions >= 1
        assert spec.min_replicates_each >= 1
        assert 0 < spec.cv_tol_pct <= 100
        assert 0 < spec.pass_fraction <= 1.0
        assert len(spec.required_well_patterns) == 1
        assert spec.required_well_patterns[0].sample_type == SampleType.SAMPLE
        assert spec.required_well_patterns[0].needs_sample_id is True

    def test_custom_values(self):
        spec = ParallelismSpec(
            min_dilutions=5,
            min_replicates_each=2,
            cv_tol_pct=15,
            pass_fraction=0.8,
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.SAMPLE,
                    needs_sample_id=True,
                )
            ],
        )
        assert spec.min_dilutions == 5
        assert spec.cv_tol_pct == 15
        assert spec.pass_fraction == 0.8

    def test_reject_cv_over_100(self):
        with pytest.raises(ValidationError) as e:
            ParallelismSpec(cv_tol_pct=101)
        assert "cv_tol_pct" in str(e.value)

    def test_reject_pass_fraction_over_1(self):
        with pytest.raises(ValidationError) as e:
            ParallelismSpec(pass_fraction=1.5)
        assert "pass_fraction" in str(e.value)

    def test_reject_min_dilutions_below_1(self):
        with pytest.raises(ValidationError) as e:
            ParallelismSpec(min_dilutions=0)
        assert "min_dilutions" in str(e.value)
