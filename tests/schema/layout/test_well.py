"""Unit tests for yassa_bio.schema.layout.well.Well"""

import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.enum import QCLevel


class TestWell:
    def _base_kwargs(self, **overrides):
        base = dict(well="A1", file_row=0, file_col=0, sample_type="sample")
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
                sample_type="calibration_standard",
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

    def test_sample_id_round_trip(self):
        w = Well(
            **self._base_kwargs(
                sample_type="sample",
                sample_id="SUBJ42_DAY1",
            )
        )
        assert w.sample_id == "SUBJ42_DAY1"

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

    @pytest.mark.parametrize("non_qc_sample_type", ["standard", "sample", "blank"])
    def test_qc_level_only_on_qc_wells(self, non_qc_sample_type):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(sample_type=non_qc_sample_type, qc_level="low"))

    def test_qc_level_allowed_on_control(self):
        w = Well(
            **self._base_kwargs(
                sample_type="quality_control",
                qc_level="high",
            )
        )
        assert w.qc_level is QCLevel.HIGH

    def test_invalid_sample_type_raises(self):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(sample_type="invalid"))

    def test_default_interferent_none(self):
        w = Well(**self._base_kwargs())
        assert w.interferent is None

    def test_interferent_string_allowed(self):
        w = Well(**self._base_kwargs(interferent="c_peptide"))
        assert w.interferent == "c_peptide"

    @pytest.mark.parametrize("bad_val", [123, ["foo"], {"id": "bar"}])
    def test_non_string_interferent_raises(self, bad_val):
        with pytest.raises(ValidationError):
            Well(**self._base_kwargs(interferent=bad_val))

    def test_carryover_allowed_on_blank(self):
        w = Well(
            **self._base_kwargs(
                well="B1",
                file_col=1,
                sample_type="blank",
                carryover=True,
            )
        )
        assert w.carryover is True
        assert w.sample_type.value == "blank"

    def test_carryover_on_non_blank_raises(self):
        with pytest.raises(ValidationError):
            Well(
                **self._base_kwargs(
                    well="B2",
                    file_col=1,
                    sample_type="sample",
                    carryover=True,
                )
            )

    def test_stability_condition_pair_ok(self):
        w = Well(
            **self._base_kwargs(
                sample_type="quality_control",
                qc_level="low",
                stability_condition="freeze-thaw",
                stability_condition_time="before",
            )
        )
        assert w.stability_condition == "freeze-thaw"
        assert w.stability_condition_time.value == "before"

    def test_stability_condition_without_time_raises(self):
        with pytest.raises(ValidationError):
            Well(
                **self._base_kwargs(
                    sample_type="quality_control",
                    qc_level="low",
                    stability_condition="freeze-thaw",
                )
            )

    def test_time_without_condition_raises(self):
        with pytest.raises(ValidationError):
            Well(
                **self._base_kwargs(
                    sample_type="quality_control",
                    qc_level="low",
                    stability_condition_time="after",
                )
            )

    @pytest.mark.parametrize(
        "sample_type,qc_level,should_raise",
        [
            ("quality_control", "mid", False),
            ("sample", None, True),
            ("quality_control", None, True),
        ],
    )
    def test_recovery_stage_rules(
        self,
        sample_type,
        qc_level,
        should_raise,
    ):
        kwargs = dict(
            well="C1",
            file_col=2,
            sample_type=sample_type,
            recovery_stage="before",
        )
        if qc_level:
            kwargs["qc_level"] = qc_level

        if should_raise:
            with pytest.raises(ValidationError):
                Well(**self._base_kwargs(**kwargs))
        else:
            w = Well(**self._base_kwargs(**kwargs))
            assert w.recovery_stage.value == "before"
            assert w.sample_type.value == "quality_control"
