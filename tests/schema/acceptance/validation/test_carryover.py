import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.carryover import CarryoverSpec
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType


class TestCarryoverSpec:
    def test_default_instantiation(self):
        spec = CarryoverSpec()
        assert len(spec.required_well_patterns) == 1
        assert spec.required_well_patterns[0].sample_type == SampleType.BLANK
        assert spec.required_well_patterns[0].carryover is True
        assert spec.min_blanks_after_uloq == 0
        assert 0 < spec.blank_thresh_pct_lloq <= 100

    def test_override_fields(self):
        spec = CarryoverSpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.BLANK,
                    carryover=True,
                )
            ],
            min_blanks_after_uloq=2,
            blank_thresh_pct_lloq=15,
        )
        assert spec.min_blanks_after_uloq == 2
        assert spec.blank_thresh_pct_lloq == 15

    def test_invalid_negative_min_blanks(self):
        with pytest.raises(ValidationError) as e:
            CarryoverSpec(min_blanks_after_uloq=-1)
        assert "min_blanks_after_uloq" in str(e.value)

    def test_invalid_blank_thresh_above_100(self):
        with pytest.raises(ValidationError) as e:
            CarryoverSpec(blank_thresh_pct_lloq=120)
        assert "blank_thresh_pct_lloq" in str(e.value)
