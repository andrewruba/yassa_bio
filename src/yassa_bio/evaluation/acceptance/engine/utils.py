import pandas as pd

from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


def check_required_well_patterns(
    df: pd.DataFrame, patterns: list[RequiredWellPattern]
) -> list[RequiredWellPattern]:
    return [p for p in patterns if not p.present(df)]


def pattern_error_dict(missing: list[RequiredWellPattern], msg: str) -> dict:
    return {
        "error": msg.format(n=len(missing)),
        "missing_patterns": [p.model_dump() for p in missing],
        "pass": False,
    }


def get_lloq_signal(calib_df: pd.DataFrame) -> float | None:
    if calib_df.empty:
        return None
    lloq_conc = calib_df["concentration"].min()
    return calib_df[calib_df["concentration"] == lloq_conc]["signal"].mean()


def compute_relative_pct(numerator: float, denominator: float | None) -> float | None:
    return (numerator / denominator * 100.0) if denominator else None
