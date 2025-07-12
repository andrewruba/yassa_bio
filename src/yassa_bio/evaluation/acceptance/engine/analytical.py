from __future__ import annotations

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical import (
    AnalyticalCalibrationSpec,
    AnalyticalQCSpec,
)
from yassa_bio.schema.layout.enum import (
    SampleType,
    QCLevel,
)


@register("acceptance", AnalyticalCalibrationSpec.__name__)
def eval_calibration(ctx: LBAContext, spec: AnalyticalCalibrationSpec) -> dict:
    cal = ctx.calib_df.copy()
    by_lvl = cal.groupby("concentration")
    cal["back_calc"] = ctx.curve_back(cal["y"].to_numpy(float))

    summary = (
        by_lvl[["x", "back_calc"]].mean().rename(columns={"back_calc": "back_mean"})
    )

    summary["bias_pct"] = (
        (summary["back_mean"] - summary["x"]).abs() / summary["x"] * 100.0
    )

    edge_levels = {summary.index.min(), summary.index.max()}
    summary["is_edge"] = summary.index.isin(edge_levels)

    tol_mid, tol_edge = spec.acc_tol_pct_mid, spec.acc_tol_pct_edge
    summary["pass"] = summary.apply(
        lambda r: r["bias_pct"] <= (tol_edge if r["is_edge"] else tol_mid), axis=1
    )

    n_levels = len(summary)
    n_pass = int(summary["pass"].sum())
    frac_pass = n_pass / n_levels if n_levels else 0.0

    failing_levels = summary[~summary["pass"]].index
    n_fail = len(failing_levels)
    n_retained = n_levels - n_fail

    can_refit = n_retained >= spec.min_retained_levels

    overall_pass = (
        can_refit
        and frac_pass >= spec.pass_fraction
        and n_fail == 0
        and n_levels >= spec.min_levels
    )

    return {
        "num_levels": n_levels,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "failing_levels": failing_levels.tolist(),
        "per_level": summary[["bias_pct", "pass"]].to_dict(orient="index"),
        "can_refit": can_refit,
        "pass": overall_pass,
    }


@register("acceptance", AnalyticalQCSpec.__name__)
def eval_qc(ctx: LBAContext, spec: AnalyticalQCSpec) -> dict:
    df = ctx.data
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL.value].copy()

    missing = [pat for pat in spec.required_well_patterns if not pat.present(qc_df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required QC pattern(s)",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    qc_df["back_calc"] = ctx.curve_back(qc_df["y"].to_numpy(float))

    qc_df["bias_pct"] = (qc_df["back_calc"] - qc_df["x"]).abs() / qc_df["x"] * 100.0
    qc_df["ok"] = qc_df["bias_pct"] <= spec.qc_tol_pct

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
