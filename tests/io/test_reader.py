from __future__ import annotations
import io
from pathlib import Path
import pandas as pd
import pytest

from yassa_bio.io.reader import _infer_format, read_csv, read_excel
from yassa_bio.core.registry import get


META_LINES = [
    "Instrument,SpectraMax iD3,,,,,,,,,,,",
    "Read Time,2025-06-19 05:57:22,,,,,,,,,,,",
    "User,lab_user42,,,,,,,,,,,",
    "Wavelength,450 nm,,,,,,,,,,,",
    "Protocol,EZHNPY-25K Human NPY ELISA,,,,,,,,,,,",
    ",,,,,,,,,,,,",
    "Row,1,2,3,4,5,6,7,8,9,10,11,12",
]

PLATE_LINES = [
    "A,0.640,0.630,0.642,0.655,0.629,0.629,0.656,0.644,0.625,0.640,0.625,0.625",
    "B,0.636,0.603,0.606,0.624,0.617,0.637,0.618,0.611,0.654,0.629,0.633,0.611",
    "C,0.624,0.634,0.615,0.638,0.623,0.628,0.623,0.660,0.632,0.616,0.644,0.614",
    "D,0.635,0.603,0.612,0.635,0.643,0.635,0.630,0.628,0.610,0.621,0.625,0.648",
    "E,0.637,0.606,0.637,0.626,0.622,0.641,0.648,0.646,0.619,0.627,0.637,0.647",
    "F,0.625,0.629,0.615,0.614,0.644,0.652,0.631,0.647,0.637,0.622,0.637,0.655",
    "G,0.632,0.656,0.593,0.644,0.633,0.628,0.633,0.602,0.629,0.637,0.654,0.624",
    "H,0.620,0.625,0.646,0.637,0.624,0.640,0.634,0.647,0.622,0.627,0.626,0.610",
]


def _build_df() -> pd.DataFrame:
    csv_text = "\n".join(META_LINES + PLATE_LINES)
    return pd.read_csv(io.StringIO(csv_text), header=None, dtype=str)


@pytest.fixture(scope="module")
def csv_file(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("io_reader") / "plate.csv"
    _build_df().to_csv(path, header=False, index=False)
    return path


@pytest.fixture(scope="module")
def xlsx_file(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("io_reader") / "plate.xlsx"
    df = _build_df()
    with pd.ExcelWriter(path, engine="openpyxl") as xls:
        for i in range(3):
            df.to_excel(xls, sheet_name=f"Run{i + 1}", header=False, index=False)
    return path


class TestInferFormat:
    @pytest.mark.parametrize(
        "fname, expected",
        [
            ("foo.csv", "csv"),
            ("foo.CSV", "csv"),
            ("foo.txt", "csv"),
            ("foo.xls", "excel"),
            ("foo.XLSX", "excel"),
        ],
    )
    def test_happy_paths(self, fname: str, expected: str):
        assert _infer_format(Path(fname)) == expected

    def test_bad_extension_raises(self):
        with pytest.raises(ValueError):
            _infer_format(Path("foo.bad"))


class TestReadCsv:
    def test_returns_dataframe_and_values(self, csv_file: Path):
        df = read_csv(csv_file)

        assert df.shape == (15, 13)
        assert df.iloc[7, 1] == "0.640"


class TestReadExcel:
    def test_sheet0_matches_csv(self, csv_file: Path, xlsx_file: Path):
        df_excel = read_excel(xlsx_file, sheet_index=0)
        df_csv = read_csv(csv_file)
        pd.testing.assert_frame_equal(df_excel, df_csv)

    def test_sheet2_equals_sheet0(self, xlsx_file: Path):
        df0 = read_excel(xlsx_file, sheet_index=0)
        df2 = read_excel(xlsx_file, sheet_index=2)
        pd.testing.assert_frame_equal(df0, df2)


class TestRegistry:
    def test_plugins_registered(self):
        assert get("reader", "csv") is read_csv
        assert get("reader", "excel") is read_excel
