from datetime import datetime
import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.file import PlateReaderFile


class TestPlateReaderFile:
    def test_minimal_valid(self):
        prf = PlateReaderFile(filepath="plate.csv")
        assert prf.filepath == "plate.csv"
        assert prf.run_date is None
        assert prf.instrument is None
        assert prf.operator is None

    def test_all_fields_round_trip(self):
        ts = datetime(2025, 6, 19, 5, 57, 22)
        prf = PlateReaderFile(
            filepath="plate.csv",
            run_date=ts,
            instrument="SpectraMax iD5",
            operator="AR",
        )

        assert prf.filepath == "plate.csv"
        assert prf.run_date == ts
        assert prf.instrument == "SpectraMax iD5"
        assert prf.operator == "AR"

    def test_run_date_serializes_to_iso(self):
        ts = datetime(2025, 6, 19, 5, 57, 22)
        prf = PlateReaderFile(filepath="plate.csv", run_date=ts)
        dumped = prf.model_dump(mode="json")
        assert dumped["run_date"] == ts.isoformat()

    def test_optional_fields_can_be_none(self):
        prf = PlateReaderFile(filepath="plate.csv")
        assert prf.filepath == "plate.csv"
        assert prf.run_date is None
        assert prf.instrument is None
        assert prf.operator is None

    def test_filepath_is_required(self):
        with pytest.raises(ValidationError):
            PlateReaderFile()

        with pytest.raises(ValidationError):
            PlateReaderFile(filepath=None)

    @pytest.mark.parametrize("bad_ts", ["not-a-date", object()])
    def test_run_date_invalid_types_raise(self, bad_ts):
        with pytest.raises(ValidationError):
            PlateReaderFile(filepath="plate.csv", run_date=bad_ts)
