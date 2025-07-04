import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.plate import Plate
from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.standard import StandardSeries
from yassa_bio.schema.layout.enum import PlateFormat, SampleType


class TestPlate:
    def _make_wells(self, n=2):
        return [
            Well(well=f"A{i + 1}", file_row=0, file_col=i, sample_type="sample")
            for i in range(n)
        ]

    def test_minimal_plate_defaults(self):
        p = Plate(plate_id="P1", wells=self._make_wells(1))
        assert p.plate_format == PlateFormat.FMT_96
        assert p.sheet_index == 0
        assert p.standards is None

    def test_all_fields_round_trip(self):
        wells = self._make_wells(3)
        stds = StandardSeries(
            start_concentration=1000, dilution_factor=3.16, num_levels=8
        )
        p = Plate(
            plate_id="EZHNPY-25K",
            sheet_index=2,
            plate_format=384,
            wells=wells,
            standards=stds,
        )
        assert p.plate_id == "EZHNPY-25K"
        assert p.sheet_index == 2
        assert p.plate_format == PlateFormat.FMT_384
        assert p.standards == stds
        assert len(p.wells) == 3

    @pytest.mark.parametrize("bad_index", [-1, -5])
    def test_negative_sheet_index_raises(self, bad_index):
        with pytest.raises(ValidationError):
            Plate(plate_id="P2", sheet_index=bad_index, wells=self._make_wells(1))

    @pytest.mark.parametrize("bad_format", [100, 640, "99"])
    def test_bad_plate_format_raises(self, bad_format):
        with pytest.raises(ValidationError):
            Plate(plate_id="P2", plate_format=bad_format, wells=self._make_wells(1))

    def test_missing_plate_id_raises(self):
        with pytest.raises(ValidationError):
            Plate(wells=self._make_wells(1))

    def test_wells_can_be_empty(self):
        p = Plate(plate_id="EMPTY", wells=[])
        assert p.wells == []

    def test_non_well_object_in_wells_raises(self):
        with pytest.raises(ValidationError):
            Plate(plate_id="Bad", wells=[123])

    def test_invalid_nested_well_bubbles_up(self):
        bad_well_dict = {
            "well": "ZZ0",
            "file_row": 0,
            "file_col": 0,
            "sample_type": "sample",
        }
        with pytest.raises(ValidationError):
            Plate(plate_id="Bad", wells=[bad_well_dict])


class TestStandardConcentrationValidator:
    def cs_well(self, idx: int | None = None, conc: float | None = None) -> Well:
        return Well(
            well=f"A{idx or 1}",
            file_row=0,
            file_col=(idx or 1) - 1,
            sample_type=SampleType.CALIBRATION_STANDARD,
            level_idx=idx,
            concentration=conc,
            concentration_units="ng/mL" if conc is not None else None,
        )

    def sample_well(self) -> Well:
        return Well(well="B1", file_row=1, file_col=0, sample_type="sample")

    def test_series_map_allows_level_idx(self):
        """Calibration standards with level_idx inside series pass validation."""
        series = StandardSeries(
            start_concentration=100, dilution_factor=2, num_levels=3
        )
        plate = Plate(
            plate_id="P-OK1",
            wells=[
                self.cs_well(idx=1),
                self.cs_well(idx=2),
                self.cs_well(idx=3),
                self.sample_well(),
            ],
            standards=series,
        )
        assert plate.standards == series

    def test_override_concentration_without_series(self):
        """Per-well concentration override is sufficient when no series present."""
        plate = Plate(
            plate_id="P-OK2",
            wells=[self.cs_well(conc=25.0), self.sample_well()],
        )
        assert plate.wells[0].concentration == 25.0

    def test_missing_concentration_raises(self):
        """Calibration standard lacking both series and override must fail."""
        with pytest.raises(ValidationError):
            Plate(
                plate_id="P-BAD1",
                wells=[self.cs_well(), self.sample_well()],
            )

    def test_level_idx_out_of_range_raises(self):
        """level_idx outside series.num_levels should fail."""
        series = StandardSeries(
            start_concentration=100, dilution_factor=2, num_levels=2
        )
        with pytest.raises(ValidationError):
            Plate(
                plate_id="P-BAD2",
                standards=series,
                wells=[self.cs_well(idx=3), self.sample_well()],
            )

    def test_non_standard_with_level_idx_without_conc_raises(self):
        """Non-standard wells must not rely on level_idx implicitly."""
        bad_qc = Well(
            well="C1",
            file_row=2,
            file_col=0,
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=1,
        )
        with pytest.raises(ValidationError):
            Plate(plate_id="P-BAD3", wells=[bad_qc, self.sample_well()])
