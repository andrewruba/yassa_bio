from __future__ import annotations

import pytest
from pydantic import ValidationError
from datetime import datetime

from yassa_bio.schema.layout.batch import Batch
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.plate import Plate
from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.enum import SampleType, PlateFormat


class TestBatch:
    def _make_plate_reader_file(self, key: str) -> PlateReaderFile:
        return PlateReaderFile(
            filepath=f"/tmp/{key}.xlsx",
            run_date=datetime(2024, 1, 1, 12, 0, 0),
            instrument="SpectraMax-iD5",
            operator="AR",
        )

    def _make_plate(self, plate_id: str, file_key: str) -> Plate:
        return Plate(
            plate_id=plate_id,
            file_key=file_key,
            plate_format=PlateFormat.FMT_96,
            wells=[
                Well(well="A1", file_row=0, file_col=0, sample_type=SampleType.BLANK)
            ],
        )

    def test_single_plate_batch_ok(self):
        prf = self._make_plate_reader_file("run1")
        plate = self._make_plate("Plate-01", "run1")

        batch = Batch(files={"run1": prf}, plates=[plate])

        assert len(batch.plates) == 1
        assert batch.plates[0].plate_id == "Plate-01"
        assert batch.plates[0].file_key in batch.files
        assert batch.files["run1"].filepath.endswith("run1.xlsx")

    def test_multiple_plates_multiple_files_ok(self):
        files = {k: self._make_plate_reader_file(k) for k in ("fileA", "fileB")}
        plates = [
            self._make_plate("P1", "fileA"),
            self._make_plate("P2", "fileB"),
        ]

        batch = Batch(files=files, plates=plates)

        assert {p.file_key for p in batch.plates} == {"fileA", "fileB"}

    def test_plate_with_unknown_file_key_raises(self):
        prf = self._make_plate_reader_file("good")
        bad_plate = self._make_plate("BadPlate", "missing_key")

        with pytest.raises(ValidationError):
            Batch(files={"good": prf}, plates=[bad_plate])

    @pytest.mark.parametrize("bad_item", [123, "not_a_plate", None, {"plate_id": "P"}])
    def test_non_plate_items_raise(self, bad_item):
        prf = self._make_plate_reader_file("run")
        with pytest.raises(ValidationError):
            Batch(files={"run": prf}, plates=[bad_item])

    def test_nested_plate_validation_bubbles_up(self):
        prf = self._make_plate_reader_file("run")
        bad_plate_dict = {
            "plate_id": "Bad",
            "file_key": "run",
            "wells": [
                {
                    "well": "ZZ0",
                    "file_row": 0,
                    "file_col": 0,
                    "sample_type": "blank",
                }
            ],
        }

        with pytest.raises(ValidationError):
            Batch(files={"run": prf}, plates=[bad_plate_dict])

    def test_empty_batch_allowed(self):
        batch = Batch(files={}, plates=[])
        assert batch.plates == []
