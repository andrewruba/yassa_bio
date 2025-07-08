from __future__ import annotations
from datetime import datetime
import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import SampleType, PlateFormat


class TestBatchData:
    @staticmethod
    def _make_reader_file(name: str) -> PlateReaderFile:
        return PlateReaderFile(
            path=f"/tmp/{name}.xlsx",
            run_date=datetime(2024, 1, 1, 12, 0, 0),
            instrument="SpectraMax-iD5",
            operator="AR",
        )

    @staticmethod
    def _make_layout() -> PlateLayout:
        """Minimal, 1-well layout that passes validation."""
        return PlateLayout(
            plate_format=PlateFormat.FMT_96,
            wells=[
                WellTemplate(
                    well="A1",
                    file_row=0,
                    file_col=0,
                    sample_type=SampleType.BLANK,
                )
            ],
        )

    def _make_plate(self, plate_id: str, file_name: str) -> PlateData:
        return PlateData(
            source_file=self._make_reader_file(file_name),
            plate_id=plate_id,
            layout=self._make_layout(),
        )

    def test_single_plate_batch_ok(self):
        plate = self._make_plate("Plate-01", "run1")
        batch = BatchData(plates=[plate])

        assert len(batch.plates) == 1
        assert batch.plates[0].plate_id == "Plate-01"
        assert batch.plates[0].source_file.path.name.endswith("run1.xlsx")

    def test_multiple_plates_batch_ok(self):
        plates = [
            self._make_plate("P1", "fileA"),
            self._make_plate("P2", "fileB"),
        ]
        batch = BatchData(plates=plates)

        assert {p.plate_id for p in batch.plates} == {"P1", "P2"}

    @pytest.mark.parametrize("bad_item", [123, "not_a_plate", None, {"plate_id": "P"}])
    def test_non_plate_items_raise(self, bad_item):
        with pytest.raises(ValidationError):
            BatchData(plates=[bad_item])

    def test_nested_plate_validation_bubbles_up(self):
        bad_plate_dict = {
            "source_file": self._make_reader_file("run_bad"),
            "plate_id": "Bad",
            "layout": {
                "plate_format": 96,
                "wells": [
                    {
                        "well": "ZZ0",
                        "file_row": 0,
                        "file_col": 0,
                        "sample_type": "blank",
                    }
                ],
            },
        }
        with pytest.raises(ValidationError):
            BatchData(plates=[bad_plate_dict])

    def test_empty_batch_allowed(self):
        batch = BatchData(plates=[])
        assert batch.plates == []
