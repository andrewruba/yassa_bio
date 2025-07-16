import pandas as pd
from typing import Any

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.specificity import SpecificitySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_lloq_signal,
    compute_relative_pct,
)


@register("acceptance", SpecificitySpec.__name__)
def eval_specificity(ctx: LBAContext, spec: SpecificitySpec) -> dict:
    df = ctx.data.copy()
    results: dict[str, Any] = {}

    # Check required well patterns
    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(
            missing, "Missing {n} required well pattern(s) with interferent"
        )

    # Blank with interferent vs LLOQ calibration signal
    blank_with_int = df[
        (df["sample_type"] == SampleType.BLANK) & (df["interferent"].notna())
    ]
    lloq_signal = get_lloq_signal(ctx.calib_df)
    blank_signal = blank_with_int["signal"].mean()
    blank_pct_of_lloq = compute_relative_pct(blank_signal, lloq_signal)
    blank_pass = (
        blank_pct_of_lloq is not None and blank_pct_of_lloq < spec.blank_thresh_pct_lloq
    )

    results["blank_pct_of_lloq"] = blank_pct_of_lloq
    results["blank_pass"] = blank_pass

    # Accuracy checks (LLOQ and ULOQ)
    for level in [QCLevel.LLOQ, QCLevel.ULOQ]:
        acc = compute_interferent_accuracy(df, level)
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
    df: pd.DataFrame, level: QCLevel, signal_col="signal"
) -> dict | None:
    """Compare signals at a QC level with vs. without interferents."""
    interfered = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == level)
        & (df["interferent"].notna())
    ]
    clean = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == level)
        & (df["interferent"].isna())
    ]

    if interfered.empty or clean.empty:
        return None

    clean_mean = clean[signal_col].mean()
    interfered_mean = interfered[signal_col].mean()
    accuracy_pct = compute_relative_pct(abs(interfered_mean - clean_mean), clean_mean)

    return {
        "accuracy_pct": accuracy_pct,
        "pass": None,  # Filled in by caller
        "interferents": sorted(interfered["interferent"].dropna().unique().tolist()),
        "clean_n": len(clean),
        "interfered_n": len(interfered),
    }
