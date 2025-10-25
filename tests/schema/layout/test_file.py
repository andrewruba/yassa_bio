from datetime import datetime
import pytest
from pathlib import Path
from pydantic import ValidationError

from yassa_bio.schema.layout.file import FileRef, PlateReaderFile


class DummyFile(FileRef):
    """Concrete for testing FileRef validators only."""

    pass


class TestFileRef:
    def test_path_normalizes_with_as_path(self, tmp_path: Path):
        d = DummyFile(path="foo/bar.txt")
        assert isinstance(d.path, Path)
        assert d.path.is_absolute()
        p = tmp_path / "in.txt"
        d2 = DummyFile(path=p)
        assert d2.path == p.resolve()

    def test_path_required_and_non_null(self):
        with pytest.raises(ValidationError):
            DummyFile()

        with pytest.raises(ValidationError):
            DummyFile(path=None)

    def test_model_dump_roundtrip_includes_path(self, tmp_path: Path):
        p = tmp_path / "x.csv"
        d = DummyFile(path=p)
        dumped = d.model_dump()
        assert "path" in dumped
        assert Path(dumped["path"]) == p.resolve()

    def test_model_dump_json_renders_path_as_string(self, tmp_path: Path):
        p = tmp_path / "x.csv"
        d = DummyFile(path=p)
        dumped = d.model_dump(mode="json")
        assert isinstance(dumped["path"], str)
        assert Path(dumped["path"]).resolve() == p.resolve()


class TestPlateReaderFile:
    def test_minimal_valid(self, tmp_path: Path):
        p = tmp_path / "plate.csv"
        prf = PlateReaderFile(path=p)
        assert prf.path == p.resolve()
        assert prf.run_date is None
        assert prf.instrument is None
        assert prf.operator is None

    def test_accepts_str_and_normalizes(self):
        prf = PlateReaderFile(path="plate.csv")
        assert prf.path.is_absolute()
        assert prf.path.name == "plate.csv"

    def test_all_fields_round_trip(self, tmp_path: Path):
        ts = datetime(2025, 6, 19, 5, 57, 22)
        p = tmp_path / "plate.csv"
        prf = PlateReaderFile(
            path=p,
            run_date=ts,
            instrument="SpectraMax iD5",
            operator="AR",
        )
        assert prf.path == p.resolve()
        assert prf.run_date == ts
        assert prf.instrument == "SpectraMax iD5"
        assert prf.operator == "AR"

    def test_run_date_serializes_to_iso(self, tmp_path: Path):
        ts = datetime(2025, 6, 19, 5, 57, 22)
        p = tmp_path / "plate.csv"
        prf = PlateReaderFile(path=p, run_date=ts)
        dumped = prf.model_dump(mode="json")
        assert dumped["run_date"] == ts.isoformat()

    def test_optional_fields_can_be_none(self, tmp_path: Path):
        prf = PlateReaderFile(path=tmp_path / "plate.csv")
        assert prf.run_date is None
        assert prf.instrument is None
        assert prf.operator is None

    def test_path_is_required(self):
        with pytest.raises(ValidationError):
            PlateReaderFile()
        with pytest.raises(ValidationError):
            PlateReaderFile(path=None)

    @pytest.mark.parametrize("bad_ts", ["not-a-date", object()])
    def test_run_date_invalid_types_raise(self, bad_ts, tmp_path: Path):
        with pytest.raises(ValidationError):
            PlateReaderFile(path=tmp_path / "plate.csv", run_date=bad_ts)
