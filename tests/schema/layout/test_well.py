import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import QCLevel


class TestWellTemplate:
    def _base_kwargs(self, **overrides):
        base = dict(well="A1", file_row=0, file_col=0, sample_type="sample")
        base.update(overrides)
        return base

    def test_basic_valid_well(self):
        w = WellTemplate(**self._base_kwargs())
        assert w.well == "A1"
        assert w.exclude is False

    def test_well_id_trim_and_uppercase(self):
        w = WellTemplate(**self._base_kwargs(well="  a12 "))
        assert w.well == "A12"

    def test_exclude_with_reason_ok(self):
        w = WellTemplate(**self._base_kwargs(exclude=True, exclude_reason="bubble"))
        assert w.exclude and w.exclude_reason == "bubble"

    def test_concentration_with_units_ok(self):
        w = WellTemplate(
            **self._base_kwargs(
                sample_type="calibration_standard",
                concentration=5.5,
                concentration_units="ng/mL",
            )
        )
        assert w.concentration == 5.5
        assert w.concentration_units == "ng/mL"

    def test_optional_numerics_ok(self):
        w = WellTemplate(
            **self._base_kwargs(
                sample_type="calibration_standard", replicate=2, level_idx=1
            )
        )
        assert w.replicate == 2
        assert w.level_idx == 1

    @pytest.mark.parametrize("bad_id", ["1A", "AA0", "!!!", "A"])
    def test_bad_well_ids_raise(self, bad_id):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(well=bad_id))

    @pytest.mark.parametrize("field, value", [("file_row", -1), ("file_col", -2)])
    def test_negative_row_or_col_raise(self, field, value):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(**{field: value}))

    @pytest.mark.parametrize("bad_rep", [0, -1])
    def test_replicate_must_be_ge_1(self, bad_rep):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(replicate=bad_rep))

    @pytest.mark.parametrize("bad_level", [0, -3])
    def test_level_idx_must_be_ge_1(self, bad_level):
        with pytest.raises(ValidationError):
            WellTemplate(
                **self._base_kwargs(
                    sample_type="calibration_standard", level_idx=bad_level
                )
            )

    def test_exclude_without_reason_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(exclude=True))

    def test_units_without_concentration_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(concentration_units="ng/mL"))

    def test_concentration_without_units_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(concentration=7.5))

    @pytest.mark.parametrize("non_qc_sample_type", ["standard", "sample", "blank"])
    def test_qc_level_only_on_qc_wells(self, non_qc_sample_type):
        with pytest.raises(ValidationError):
            WellTemplate(
                **self._base_kwargs(sample_type=non_qc_sample_type, qc_level="low")
            )

    def test_qc_level_allowed_on_control(self):
        w = WellTemplate(
            **self._base_kwargs(
                sample_type="quality_control",
                qc_level="high",
            )
        )
        assert w.qc_level is QCLevel.HIGH

    def test_invalid_sample_type_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(sample_type="invalid"))

    def test_std_without_level_or_conc_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(sample_type="calibration_standard"))

    def test_nonstandard_with_level_idx_raises(self):
        with pytest.raises(ValidationError):
            WellTemplate(**self._base_kwargs(sample_type="sample", level_idx=1))

    def test_record_property_matches_dump(self):
        w = WellTemplate(
            **self._base_kwargs(replicate=2, exclude=True, exclude_reason="bubble")
        )
        dumped = w.model_dump()
        assert w.record == dumped
