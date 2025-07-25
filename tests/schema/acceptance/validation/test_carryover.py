import pytest
from pydantic import ValidationError

from yassa_bio.schema.acceptance.validation.carryover import ValidationCarryoverSpec
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType


class TestValidationCarryoverSpec:
    def test_default_instantiation(self):
        spec = ValidationCarryoverSpec()
        assert len(spec.required_well_patterns) == 1
        assert spec.required_well_patterns[0].sample_type == SampleType.BLANK
        assert spec.required_well_patterns[0].carryover is True
        assert spec.min_blanks_after_uloq == 0

    def test_override_fields(self):
        spec = ValidationCarryoverSpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.BLANK,
                    carryover=True,
                )
            ],
            min_blanks_after_uloq=2,
        )
        assert spec.min_blanks_after_uloq == 2

    def test_invalid_negative_min_blanks(self):
        with pytest.raises(ValidationError) as e:
            ValidationCarryoverSpec(min_blanks_after_uloq=-1)
        assert "min_blanks_after_uloq" in str(e.value)
