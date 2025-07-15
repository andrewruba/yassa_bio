import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.parallelism import ParallelismSpec
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType


class TestParallelismSpec:
    def test_valid_instantiation(self):
        spec = ParallelismSpec()
        assert spec.min_dilutions >= 1
        assert spec.min_replicates >= 1
        assert 0 < spec.cv_tol_pct <= 100
        assert len(spec.required_well_patterns) == 1
        assert spec.required_well_patterns[0].sample_type == SampleType.SAMPLE

    def test_custom_values(self):
        spec = ParallelismSpec(
            min_dilutions=5,
            min_replicates=2,
            cv_tol_pct=15,
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.SAMPLE,
                )
            ],
        )
        assert spec.min_dilutions == 5
        assert spec.cv_tol_pct == 15

    def test_reject_cv_over_100(self):
        with pytest.raises(ValidationError) as e:
            ParallelismSpec(cv_tol_pct=101)
        assert "cv_tol_pct" in str(e.value)

    def test_reject_min_dilutions_below_0(self):
        with pytest.raises(ValidationError) as e:
            ParallelismSpec(min_dilutions=-1)
        assert "min_dilutions" in str(e.value)
