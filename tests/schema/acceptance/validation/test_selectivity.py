import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.selectivity import SelectivitySpec
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


class TestSelectivitySpec:
    def test_valid_instantiation(self):
        spec = SelectivitySpec()

        assert spec.min_sources >= 1
        assert 0.0 < spec.pass_fraction <= 1.0
        assert spec.blank_thresh_pct_lloq < 100
        assert spec.acc_tol_pct_lloq < 100
        assert spec.acc_tol_pct_high < 100

        patterns = spec.required_well_patterns
        assert isinstance(patterns, list)
        assert len(patterns) >= 3
        assert any(
            p.sample_type == SampleType.BLANK and p.needs_matrix_type for p in patterns
        )
        assert any(
            p.qc_level == QCLevel.LLOQ
            for p in patterns
            if p.sample_type == SampleType.QUALITY_CONTROL
        )

    def test_custom_instantiation(self):
        spec = SelectivitySpec(
            min_sources=5,
            pass_fraction=0.9,
            blank_thresh_pct_lloq=10,
            acc_tol_pct_lloq=15,
            acc_tol_pct_high=12,
            required_well_patterns=[
                RequiredWellPattern(sample_type=SampleType.BLANK),
            ],
        )

        assert spec.min_sources == 5
        assert spec.pass_fraction == 0.9
        assert spec.blank_thresh_pct_lloq == 10
        assert spec.acc_tol_pct_lloq == 15
        assert spec.acc_tol_pct_high == 12
        assert len(spec.required_well_patterns) == 1

    def test_invalid_pass_fraction(self):
        with pytest.raises(ValidationError) as e:
            SelectivitySpec(pass_fraction=1.5)
        assert "pass_fraction" in str(e.value)

    def test_invalid_blank_thresh(self):
        with pytest.raises(ValidationError) as e:
            SelectivitySpec(blank_thresh_pct_lloq=-1)
        assert "blank_thresh_pct_lloq" in str(e.value)

    def test_invalid_min_sources(self):
        with pytest.raises(ValidationError) as e:
            SelectivitySpec(min_sources=0)
        assert "min_sources" in str(e.value)
