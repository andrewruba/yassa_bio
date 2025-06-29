from typing import Any
from pydantic import Field


def Percent(default: float | None = None, *, lo: float = 0, hi: float = 100, **kw: Any):
    """
    Constrain a numeric field to [lo, hi].
    """
    return Field(default, ge=lo, le=hi, **kw)


def Fraction01(default: float = 1.0, **kw: Any):
    """
    Useful for probabilities or fractions.
    0 ≤ x ≤ 1
    """
    return Field(default, ge=0, le=1, **kw)
