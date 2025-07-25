import pandas as pd
from typing import Any

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.specificity import ValidationSpecificitySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel, CalibrationLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_scalar,
    get_calibration_signal_for_level,
)


@register("acceptance", ValidationSpecificitySpec.__name__)
def eval_specificity(ctx: LBAContext, spec: ValidationSpecificitySpec) -> dict:
    df = ctx.data.copy()
    results: dict[str, Any] = {}

    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(
            missing, "Missing {n} required well pattern(s) with interferent"
        )

    # Check blank w/ interferent < LLOQ
    blank_with_int = df[
        (df["sample_type"] == SampleType.BLANK) & (df["interferent"].notna())
    ]
    lloq_signal = get_calibration_signal_for_level(ctx.calib_df, CalibrationLevel.LLOQ)
    blank_signal = blank_with_int["signal"].mean()
    blank_pass = blank_signal < lloq_signal if lloq_signal is not None else False
    results["blank_signal"] = blank_signal
    results["lloq_signal"] = lloq_signal
    results["blank_pass"] = blank_pass

    # Check LLOQ/ULOQ w/ interferent accuracy
    for level in [QCLevel.LLOQ, QCLevel.ULOQ]:
        acc = compute_interferent_accuracy(df, ctx.calib_df, level)
        if acc:
            acc["pass"] = acc["accuracy_pct"] <= spec.acc_tol_pct
        else:
            acc = {"error": f"Insufficient {level.value.upper()} data", "pass": False}
        results[f"{level.value}_accuracy"] = acc

    # Overall pass/fail
    results["pass"] = (
        results["blank_pass"]
        and results["lloq_accuracy"]["pass"]
        and results["uloq_accuracy"]["pass"]
    )

    return results


def compute_interferent_accuracy(
    df: pd.DataFrame, calib_df: pd.DataFrame, level: QCLevel
) -> dict | None:
    """Compare signals at a QC level with vs. without interferents."""
    interfered = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == level)
        & (df["interferent"].notna())
    ]

    if interfered.empty:
        return None

    clean_mean = get_calibration_signal_for_level(calib_df, level)
    interfered_mean = interfered["signal"].mean()
    accuracy_pct = compute_relative_pct_scalar(
        abs(interfered_mean - clean_mean), clean_mean
    )

    return {
        "accuracy_pct": accuracy_pct,
        "pass": None,  # Filled in by caller
        "interferents": sorted(interfered["interferent"].dropna().unique().tolist()),
        "interfered_n": len(interfered),
    }
