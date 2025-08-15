from __future__ import annotations
from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical.calibration import AnalyticalCalibrationSpec
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_vectorized,
)


@register("acceptance", AnalyticalCalibrationSpec.__name__)
def eval_calibration(ctx: LBAContext, spec: AnalyticalCalibrationSpec) -> dict:
    cal = ctx.calib_df.copy()

    # Ensure required well patterns are present
    missing = check_required_well_patterns(cal, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(
            missing, "Missing {n} required calibration pattern(s)"
        )

    # Back-calculate concentrations
    cal["back_calc"] = ctx.curve_back(cal["y"].to_numpy(float))

    # Group by level and calculate bias
    by_lvl = cal.groupby("concentration")
    summary = (
        by_lvl[["x", "back_calc"]].mean().rename(columns={"back_calc": "back_mean"})
    )
    summary["acc_pct"] = compute_relative_pct_vectorized(
        (summary["back_mean"] - summary["x"]).abs(), summary["x"]
    )

    # Flag edge levels and assess tolerance
    edge_levels = {summary.index.min(), summary.index.max()}
    summary["is_edge"] = summary.index.isin(edge_levels)
    summary["pass"] = summary.apply(
        lambda r: r["acc_pct"]
        <= (spec.acc_tol_pct_edge if r["is_edge"] else spec.acc_tol_pct_mid),
        axis=1,
    )

    # Compute overall pass/fail
    n_levels = len(summary)
    n_pass = int(summary["pass"].sum())
    frac_pass = n_pass / n_levels if n_levels else 0.0
    failing_levels = summary[~summary["pass"]].index
    n_retained = n_levels - len(failing_levels)
    can_refit = n_retained >= spec.min_retained_levels
    overall_pass = (
        can_refit
        and frac_pass >= spec.pass_fraction
        and len(failing_levels) == 0
        and n_levels >= spec.min_levels
    )

    return {
        "num_levels": n_levels,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "failing_levels": failing_levels.tolist(),
        "per_level": summary[["acc_pct", "pass"]].to_dict(orient="index"),
        "can_refit": can_refit,
        "pass": overall_pass,
    }
