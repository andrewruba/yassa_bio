from __future__ import annotations
from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical.qc import QCSpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_vectorized,
)


@register("acceptance", QCSpec.__name__)
def eval_qc(ctx: LBAContext, spec: QCSpec) -> dict:
    df = ctx.data
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL.value].copy()

    # Check required QC well patterns
    missing = check_required_well_patterns(qc_df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(missing, "Missing {n} required QC pattern(s)")

    # Compute per-well accuracy
    qc_df["back_calc"] = ctx.curve_back(qc_df["y"].to_numpy(float))
    qc_df["acc_pct"] = compute_relative_pct_vectorized(
        (qc_df["back_calc"] - qc_df["x"]).abs(), qc_df["x"]
    )
    qc_df["ok"] = qc_df["acc_pct"] <= spec.acc_tol_pct

    # Summarize by QC level
    n_total = len(qc_df)
    n_pass_total = int(qc_df["ok"].sum())
    frac_pass_total = n_pass_total / n_total if n_total else 0.0
    per_level: dict[str, dict] = {}
    failing_idxs: list[int] = []

    for lvl in (QCLevel.LOW, QCLevel.MID, QCLevel.HIGH):
        sub = qc_df[qc_df["qc_level"] == lvl.value]
        n_lvl = len(sub)
        n_pass_lvl = int(sub["ok"].sum())
        frac_lvl = n_pass_lvl / n_lvl if n_lvl else 0.0

        per_level[lvl.value] = {
            "n": n_lvl,
            "num_pass": n_pass_lvl,
            "pass_frac": frac_lvl,
            "meets_level_fraction": frac_lvl >= spec.pass_fraction_each_level,
        }
        failing_idxs.extend(sub[~sub["ok"]].index.tolist())

    # Determine overall result
    overall_pass = frac_pass_total >= spec.pass_fraction_total and all(
        v["meets_level_fraction"] for v in per_level.values()
    )

    return {
        "total_wells": n_total,
        "num_pass": n_pass_total,
        "pass_fraction": frac_pass_total,
        "per_level": per_level,
        "failing_wells": failing_idxs,
        "pass": overall_pass,
    }
