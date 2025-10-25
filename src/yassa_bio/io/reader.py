from __future__ import annotations
import pandas as pd
from pathlib import Path

from yassa_bio.core.registry import register


def _infer_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".csv", ".txt"}:
        return "csv"
    if ext in {".xls", ".xlsx"}:
        return "excel"
    raise ValueError(f"Cannot infer reader for {ext!s}")


@register("reader", "csv")
def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    header = kwargs.get("header", None)
    dtype = kwargs.get("dtype", str)
    engine = kwargs.get("engine", "python")
    return pd.read_csv(path, header=header, dtype=dtype, engine=engine)


@register("reader", "excel")
def read_excel(path: Path, **kwargs) -> pd.DataFrame:
    header = kwargs.get("header", None)
    dtype = kwargs.get("dtype", str)
    engine = kwargs.get("engine", "openpyxl")
    sheet_index = kwargs.get("sheet_index", 0)
    return pd.read_excel(
        path, sheet_name=sheet_index, header=header, dtype=dtype, engine=engine
    )
