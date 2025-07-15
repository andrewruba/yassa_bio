from __future__ import annotations
import pandas as pd

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.specificity import SpecificitySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


@register("acceptance", SpecificitySpec.__name__)
def eval_specificity(ctx: LBAContext, spec: SpecificitySpec) -> dict:
    df = ctx.data.copy()

    missing = [p for p in spec.required_well_patterns if not p.present(df)]
    if missing:
        return {
            "error": (
                f"Missing {len(missing)} required well pattern(s) with interferent"
            ),
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    results = {}

    blank_with_int = df[
        (df["sample_type"] == SampleType.BLANK) & (df["interferent"].notna())
    ]

    cal = ctx.calib_df
    lloq_conc = cal["concentration"].min()
    lloq_mean_signal = cal[cal["concentration"] == lloq_conc]["signal"].mean()

    blank_signal = blank_with_int["signal"].mean()
    blank_pct_of_lloq = (
        (blank_signal / lloq_mean_signal * 100.0) if lloq_mean_signal else 0.0
    )
    blank_ok = blank_pct_of_lloq < spec.blank_thresh_pct_lloq

    results["blank_pct_of_lloq"] = blank_pct_of_lloq
    results["blank_ok"] = blank_ok

    lloq_bias = compute_interferent_bias(df, QCLevel.LLOQ)
    uloq_bias = compute_interferent_bias(df, QCLevel.ULOQ)

    if lloq_bias:
        lloq_bias["pass"] = lloq_bias["bias_pct"] <= spec.acc_tol_pct
    else:
        lloq_bias = {"error": "Insufficient LLOQ data", "pass": False}

    if uloq_bias:
        uloq_bias["pass"] = uloq_bias["bias_pct"] <= spec.acc_tol_pct
    else:
        uloq_bias = {"error": "Insufficient ULOQ data", "pass": False}

    results["lloq_bias"] = lloq_bias
    results["uloq_bias"] = uloq_bias

    results["pass"] = blank_ok and lloq_bias["pass"] and uloq_bias["pass"]

    return results


def compute_interferent_bias(
    df: pd.DataFrame, level: QCLevel, signal_col="signal"
) -> dict | None:
    """Compare signals at a QC level with vs. without interferents."""
    interfered = df[
        (df["sample_type"] == "quality_control")
        & (df["qc_level"] == level)
        & (df["interferent"].notna())
    ]
    clean = df[
        (df["sample_type"] == "quality_control")
        & (df["qc_level"] == level)
        & (df["interferent"].isna())
    ]

    if interfered.empty or clean.empty:
        return None

    clean_mean = clean[signal_col].mean()
    interfered_mean = interfered[signal_col].mean()
    bias_pct = (
        abs(interfered_mean - clean_mean) / clean_mean * 100.0 if clean_mean else 0.0
    )

    return {
        "bias_pct": bias_pct,
        "pass": None,  # to be filled in by spec evaluator
        "interferents": sorted(interfered["interferent"].dropna().unique().tolist()),
        "clean_n": len(clean),
        "interfered_n": len(interfered),
    }
