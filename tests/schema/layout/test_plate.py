from __future__ import annotations
import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.schema.layout.well import WellTemplate as Well
from yassa_bio.schema.layout.enum import PlateFormat, SampleType


def _wells(n: int = 2) -> list[Well]:
    """Create `n` generic sample wells in row A."""
    return [
        Well(well=f"A{i + 1}", file_row=0, file_col=i, sample_type="sample")
        for i in range(n)
    ]


def _layout(**kw) -> PlateLayout:
    """Convenience wrapper for PlateLayout with default wells."""
    return PlateLayout(wells=_wells(1), **kw)


class TestPlateLayout:
    def test_defaults(self):
        pl = PlateLayout(wells=_wells(1))
        assert pl.plate_format == PlateFormat.FMT_96
        assert pl.sheet_index == 0
        assert pl.standards is None

    @pytest.mark.parametrize("bad_index", [-1, -5])
    def test_negative_sheet_index_raises(self, bad_index):
        with pytest.raises(ValidationError):
            _layout(sheet_index=bad_index)

    @pytest.mark.parametrize("bad_fmt", [100, 640, "99"])
    def test_bad_plate_format_raises(self, bad_fmt):
        with pytest.raises(ValidationError):
            _layout(plate_format=bad_fmt)

    def test_empty_well_list_allowed(self):
        pl = PlateLayout(wells=[])
        assert pl.wells == []

    def test_non_well_object_raises(self):
        with pytest.raises(ValidationError):
            PlateLayout(wells=[123])

    def test_nested_well_validation_bubbles_up(self):
        bad_well = {
            "well": "ZZ0",
            "file_row": 0,
            "file_col": 0,
            "sample_type": "sample",
        }
        with pytest.raises(ValidationError):
            PlateLayout(wells=[bad_well])


class TestPlateData:
    def test_minimal_defaults(self):
        pd = PlateData(
            plate_id="P1",
            source_file=PlateReaderFile(filepath="/tmp/F1.csv"),
            layout=_layout(),
        )
        assert pd.plate_id == "P1"
        assert pd.layout.plate_format == PlateFormat.FMT_96

    def test_round_trip_all_fields(self):
        stds = StandardSeries(
            start_concentration=1000,
            dilution_factor=3.16,
            num_levels=8,
            concentration_units="ng/mL",
        )
        wells = _wells(3)
        pd = PlateData(
            plate_id="EZHNPY-25K",
            source_file=PlateReaderFile(filepath="/tmp/RAW_02.csv"),
            layout=PlateLayout(
                sheet_index=2,
                plate_format=384,
                wells=wells,
                standards=stds,
            ),
        )
        assert pd.layout.sheet_index == 2
        assert pd.layout.plate_format == PlateFormat.FMT_384
        assert pd.layout.standards == stds
        assert len(pd.layout.wells) == 3


class TestStandardConcentrationValidator:
    @staticmethod
    def cs_well(
        idx: int | None = None,
        conc: float | None = None,
        units: str | None = None,
    ) -> Well:
        return Well(
            well=f"A{idx or 1}",
            file_row=0,
            file_col=(idx or 1) - 1,
            sample_type=SampleType.CALIBRATION_STANDARD,
            level_idx=idx,
            concentration=conc,
            concentration_units=units if conc is not None else None,
        )

    @staticmethod
    def sample_well(**overrides) -> Well:
        return Well(
            well="B1",
            file_row=1,
            file_col=0,
            sample_type=SampleType.SAMPLE,
            **overrides,
        )

    def test_series_map_sets_missing_conc_fields(self):
        series = StandardSeries(
            start_concentration=100,
            dilution_factor=2,
            num_levels=3,
            concentration_units="ng/mL",
        )
        layout = PlateLayout(
            wells=[
                self.cs_well(idx=1),
                self.cs_well(idx=2),
                self.cs_well(idx=3),
                self.sample_well(),
            ],
            standards=series,
        )
        expected = [100.0, 50.0, 25.0]
        for w, e in zip(layout.wells[:3], expected):
            assert w.concentration == pytest.approx(e)
            assert w.concentration_units == "ng/mL"

    def test_override_concentration_without_series(self):
        well = self.cs_well(conc=25.0, units="ng/mL")
        layout = PlateLayout(wells=[well, self.sample_well()])
        assert layout.wells[0].concentration == 25.0

    def test_override_concentration_with_series_is_preserved(self):
        series = StandardSeries(
            start_concentration=100,
            dilution_factor=2,
            num_levels=3,
            concentration_units="ng/mL",
        )
        overriding_well = self.cs_well(conc=42.0, units="ng/mL")

        layout = PlateLayout(
            wells=[overriding_well, self.sample_well()],
            standards=series,
        )

        assert layout.wells[0].concentration == pytest.approx(42.0)
        assert layout.wells[0].concentration_units == "ng/mL"

    def test_missing_concentration_and_level_raises(self):
        with pytest.raises(ValidationError):
            PlateLayout(
                wells=[
                    Well(
                        well="A1",
                        file_row=0,
                        file_col=0,
                        sample_type=SampleType.CALIBRATION_STANDARD,
                    )
                ]
            )

    def test_level_idx_out_of_range_raises(self):
        series = StandardSeries(
            start_concentration=100,
            dilution_factor=2,
            num_levels=2,
            concentration_units="ng/mL",
        )
        with pytest.raises(ValidationError):
            PlateLayout(
                standards=series,
                wells=[self.cs_well(idx=3), self.sample_well()],
            )

    def test_non_standard_with_level_idx_raises(self):
        with pytest.raises(ValidationError):
            self.sample_well(level_idx=1)

    def test_conflicting_concentration_and_units_raise(self):
        with pytest.raises(ValidationError):
            self.cs_well(conc=5.0, units=None)

        with pytest.raises(ValidationError):
            self.cs_well(conc=None, units="ng/mL")
