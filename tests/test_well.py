"""Unit tests for yassa_bio.schema.layout.well.Well"""

import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.enum import SampleType


class TestWell:

    def _base_kwargs(self, **overrides):
        base = dict(well="A1", file_row=0, file_col=0, sample_type=SampleType.SAMPLE)
        base.update(overrides)
        return base

    def test_basic_valid_well(self):
        w = Well(**self._base_kwargs())
        assert w.well == "A1"
        assert w.exclude is False

    def test_well_id_trim_and_uppercase(self):
        w = Well(**self._base_kwargs(well="  a12 "))
        assert w.well == "A12"

    def test_exclude_with_reason_ok(self):
        w = Well(**self._base_kwargs(exclude=True, exclude_reason="bubble"))
        assert w.exclude and w.exclude_reason == "bubble"

    def test_concentration_with_units_ok(self):
        w = Well(
            **self._base_kwargs(
                sample_type=SampleType.STANDARD,
                concentration=5.5,
                concentration_units="ng/mL",
            )
        )
        assert w.concentration == 5.5
        assert w.concentration_units == "ng/mL"

    def test_optional_numerics_ok(self):
        w = Well(**self._base_kwargs(replicate=2, level_idx=1, dilution_factor=2.0))
        assert w.replicate == 2
        assert w.level_idx == 1
        assert w.dilution_factor == 2.0

    @pytest.mark.parametrize("bad_id", ["1A", "AA0", "!!!", "A"])
    def test_bad_well_ids_raise(self, bad_id):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(well=bad_id))

    @pytest.mark.parametrize("field, value", [("file_row", -1), ("file_col", -2)])
    def test_negative_row_or_col_raise(self, field, value):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(**{field: value}))

    @pytest.mark.parametrize("bad_rep", [0, -1])
    def test_replicate_must_be_ge_1(self, bad_rep):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(replicate=bad_rep))

    @pytest.mark.parametrize("bad_level", [0, -3])
    def test_level_idx_must_be_ge_1(self, bad_level):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(level_idx=bad_level))

    @pytest.mark.parametrize("bad_df", [1.0, 0.5, -2])
    def test_dilution_factor_must_be_gt_1(self, bad_df):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(dilution_factor=bad_df))

    def test_exclude_without_reason_raises(self):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(exclude=True))

    def test_units_without_concentration_raises(self):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(concentration_units="ng/mL"))

    def test_concentration_without_units_raises(self):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(concentration=7.5))

    def test_invalid_sample_type_raises(self):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(sample_type="invalid"))
