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
    return pd.read_csv(path, header=None, dtype=str, engine="python")


@register("reader", "excel")
def read_excel(path: Path, sheet_index: int = 0, **kwargs) -> pd.DataFrame:
    return pd.read_excel(
        path,
        sheet_name=sheet_index,
        header=None,
        dtype=str,
        engine="openpyxl",
    )
