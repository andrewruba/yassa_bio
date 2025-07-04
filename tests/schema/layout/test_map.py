import pytest
from pydantic import ValidationError

from yassa_bio.schema.layout.map import DataMap
from yassa_bio.schema.layout.plate import Plate
from yassa_bio.schema.layout.well import Well
from yassa_bio.schema.layout.enum import SampleType


class TestDataMap:
    def _make_plate(self, pid="P1"):
        return Plate(
            plate_id=pid,
            wells=[Well(well="A1", file_row=0, file_col=0, sample_type="blank")],
        )

    def test_single_plate_ok(self):
        plate = self._make_plate("EZHNPY-25K")
        dm = DataMap(plates=[plate])
        assert len(dm.plates) == 1
        assert dm.plates[0].plate_id == "EZHNPY-25K"

    def test_multiple_plates_ok(self):
        plates = [self._make_plate("P1"), self._make_plate("P2")]
        dm = DataMap(plates=plates)
        assert [p.plate_id for p in dm.plates] == ["P1", "P2"]

    def test_empty_plate_list_ok(self):
        dm = DataMap(plates=[])
        assert dm.plates == []
        assert len(dm.plates) == 0

    @pytest.mark.parametrize("bad_item", [123, "not_a_plate", None, {"plate_id": "P"}])
    def test_non_plate_items_raise(self, bad_item):
        with pytest.raises(ValidationError):
            DataMap(plates=[bad_item])

    def test_nested_plate_validation_bubbles_up(self):
        bad_plate_dict = {
            "plate_id": "Bad",
            "wells": [
                {
                    "well": "ZZ0",
                    "file_row": 0,
                    "file_col": 0,
                    "sample_type": SampleType.BLANK,
                }
            ],
        }
        with pytest.raises(ValidationError):
            DataMap(plates=[bad_plate_dict])
