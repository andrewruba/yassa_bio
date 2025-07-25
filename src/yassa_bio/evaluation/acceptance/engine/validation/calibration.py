import pandas as pd

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.calibration import ValidationCalibrationSpec
from yassa_bio.schema.layout.enum import CalibrationLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_calibration_concentration_for_level,
)


@register("acceptance", ValidationCalibrationSpec.__name__)
def eval_calibration_validation(
    ctx: LBAContext, spec: ValidationCalibrationSpec
) -> dict:
    df = ctx.calib_df.copy()

    if df.empty:
        return {"error": "calib_df is empty", "pass": False}

    # Check for required well patterns
    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(missing, "Missing {n} required well pattern(s)")

    # Back-calculate and compute accuracy
    df["back_calc"] = ctx.curve_back(df["y"].to_numpy(float))

    grouped = df.groupby("concentration")
    summary_rows = []

    for conc, group in grouped:
        n = len(group)
        mean_nominal = group["x"].mean()
        mean_back = group["back_calc"].mean()
        acc = abs(mean_back - mean_nominal) / mean_nominal * 100.0

        if n > 1 and mean_back != 0:
            cv = group["back_calc"].std(ddof=1) / mean_back * 100.0
        else:
            cv = 0.0

        summary_rows.append(
            {
                "concentration": conc,
                "n": n,
                "acc_pct": acc,
                "cv_pct": cv,
            }
        )

    summary_df = pd.DataFrame(summary_rows).set_index("concentration")

    # Determine edge levels
    lloq = get_calibration_concentration_for_level(df, CalibrationLevel.LLOQ)
    uloq = get_calibration_concentration_for_level(df, CalibrationLevel.ULOQ)
    edge_levels = {lloq, uloq} if lloq is not None and uloq is not None else set()
    summary_df["is_edge"] = summary_df.index.isin(edge_levels)

    # Apply accuracy and precision tolerances
    summary_df["acc_ok"] = summary_df.apply(
        lambda r: r["acc_pct"]
        <= (spec.acc_tol_pct_edge if r["is_edge"] else spec.acc_tol_pct_mid),
        axis=1,
    )
    summary_df["cv_ok"] = summary_df.apply(
        lambda r: r["cv_pct"]
        <= (spec.cv_tol_pct_edge if r["is_edge"] else spec.cv_tol_pct_mid),
        axis=1,
    )

    summary_df["pass"] = summary_df["acc_ok"] & summary_df["cv_ok"]

    # Final decision logic
    n_levels = len(summary_df)
    n_pass = int(summary_df["pass"].sum())
    frac_pass = n_pass / n_levels if n_levels else 0.0
    overall_pass = n_levels >= spec.min_levels and frac_pass >= spec.pass_fraction

    return {
        "num_levels": n_levels,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "per_level": summary_df[
            ["n", "acc_pct", "cv_pct", "is_edge", "acc_ok", "cv_ok", "pass"]
        ].to_dict(orient="index"),
        "pass": overall_pass,
    }
