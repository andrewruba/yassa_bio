import pandas as pd
from typing import Any, Dict, Callable

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.selectivity import ValidationSelectivitySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel, CalibrationLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_calibration_signal_for_level,
    compute_relative_pct_vectorized,
)


@register("acceptance", ValidationSelectivitySpec.__name__)
def eval_selectivity(ctx: LBAContext, spec: ValidationSelectivitySpec) -> dict:
    df = ctx.data.copy()

    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(missing, "Missing {n} required well pattern(s)")

    lloq_signal = get_calibration_signal_for_level(ctx.calib_df, CalibrationLevel.LLOQ)
    if lloq_signal is None:
        return {"error": "LLOQ signal could not be determined", "pass": False}

    # Group and evaluate per matrix source
    df["matrix_type"] = df["matrix_type"].fillna("normal")
    grouped = df.groupby("matrix_source_id")
    matrix_type_map = df.groupby("matrix_source_id")["matrix_type"].first()
    source_results: Dict[str, dict] = {
        sid: evaluate_source_group(
            sub, matrix_type_map[sid], lloq_signal, spec, ctx.curve_back
        )
        for sid, sub in grouped
    }

    # Summary statistics
    n_sources = len(source_results)
    n_pass = sum(r["pass"] for r in source_results.values())
    frac_pass = n_pass / n_sources if n_sources else 0.0
    overall_pass = frac_pass >= spec.pass_fraction and n_sources >= spec.min_sources

    matrix_type_counts: Dict[str, int] = {}
    for r in source_results.values():
        t = r["matrix_type"]
        matrix_type_counts[t] = matrix_type_counts.get(t, 0) + 1

    return {
        "num_sources": n_sources,
        "num_passed": n_pass,
        "pass_fraction": frac_pass,
        "matrix_types": matrix_type_counts,
        "per_source": source_results,
        "pass": overall_pass,
    }


def evaluate_source_group(
    df: pd.DataFrame,
    matrix_type: str,
    lloq_signal: float,
    spec: ValidationSelectivitySpec,
    back_calc_fn: Callable,
) -> dict:
    """Evaluate selectivity metrics for a single matrix_source_id group."""
    entry: dict[str, Any] = {"matrix_type": matrix_type}

    # Blank signal < LLOQ signal
    blank = df[df["sample_type"] == SampleType.BLANK]
    blank_signal = blank["signal"].mean()
    entry["blank_signal"] = blank_signal
    entry["blank_ok"] = blank_signal < lloq_signal if pd.notna(blank_signal) else False

    # LLOQ QC back-calculate and compute accuracy
    lloq = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == QCLevel.LLOQ)
    ].copy()
    if not lloq.empty:
        lloq["back_calc"] = back_calc_fn(lloq["y"].to_numpy(float))
        lloq["acc_pct"] = compute_relative_pct_vectorized(
            (lloq["back_calc"] - lloq["x"]).abs(), lloq["x"]
        )
        acc_mean = lloq["acc_pct"].mean()
        entry["lloq_acc_pct"] = acc_mean
        entry["lloq_ok"] = acc_mean <= spec.acc_tol_pct_lloq
    else:
        entry["lloq_acc_pct"] = None
        entry["lloq_ok"] = False

    # High QC back-calculate and compute accuracy
    high = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == QCLevel.HIGH)
    ].copy()
    if not high.empty:
        high["back_calc"] = back_calc_fn(high["y"].to_numpy(float))
        high["acc_pct"] = compute_relative_pct_vectorized(
            (high["back_calc"] - high["x"]).abs(), high["x"]
        )
        acc_mean = high["acc_pct"].mean()
        entry["high_acc_pct"] = acc_mean
        entry["high_ok"] = acc_mean <= spec.acc_tol_pct_high
    else:
        entry["high_acc_pct"] = None
        entry["high_ok"] = False

    entry["pass"] = entry["blank_ok"] and entry["lloq_ok"] and entry["high_ok"]
    return entry
