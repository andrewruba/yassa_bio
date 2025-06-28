from datetime import datetime
import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.file import FileRef


def test_defaults_only_filepath():
    fr = FileRef(filepath="plate.csv")
    assert fr.filepath == "plate.csv"
    assert fr.run_date is None
    assert fr.instrument is None
    assert fr.operator is None


def test_all_fields_round_trip():
    ts = datetime(2025, 6, 19, 5, 57, 22)
    fr = FileRef(
        filepath="/data/plate.csv",
        run_date=ts,
        instrument="SpectraMax iD5",
        operator="AR",
    )

    assert fr.filepath == "/data/plate.csv"
    assert fr.run_date == ts
    assert fr.instrument == "SpectraMax iD5"
    assert fr.operator == "AR"


def test_run_date_serializes_to_iso():
    ts = datetime(2025, 6, 19, 5, 57, 22)
    fr = FileRef(run_date=ts)
    dumped = fr.model_dump(mode="json")
    assert dumped["run_date"] == ts.isoformat()


def test_optional_fields_can_be_none():
    fr = FileRef()
    assert fr.filepath is None
    assert fr.run_date is None
    assert fr.instrument is None
    assert fr.operator is None

    fr_none = FileRef(filepath=None)
    assert fr_none.filepath is None


@pytest.mark.parametrize("bad_ts", ["not-a-date", object()])
def test_run_date_invalid_types_raise(bad_ts):
    with pytest.raises(ValidationError):
        FileRef(run_date=bad_ts)
