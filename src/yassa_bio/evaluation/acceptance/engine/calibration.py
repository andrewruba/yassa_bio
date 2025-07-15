from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.calibration import CalibrationSpec
import pandas as pd


@register("acceptance", CalibrationSpec.__name__)
def eval_calibration_validation(ctx: LBAContext, spec: CalibrationSpec) -> dict:
    cal = ctx.calib_df.copy()

    if cal.empty:
        return {"error": "calib_df is empty", "pass": False}

    # Back-calculate concentrations
    cal["back_calc"] = ctx.curve_back(cal["y"].to_numpy(float))
    cal["bias_pct"] = (cal["back_calc"] - cal["x"]).abs() / cal["x"] * 100.0

    by_lvl = cal.groupby("concentration")
    summary_rows = []

    for conc, group in by_lvl:
        n = len(group)
        mean_nominal = group["x"].mean()
        mean_back = group["back_calc"].mean()
        bias = abs(mean_back - mean_nominal) / mean_nominal * 100.0
        cv = (
            group["back_calc"].std(ddof=1) / mean_back * 100.0
            if n > 1 and mean_back != 0
            else 0.0
        )

        summary_rows.append(
            {
                "concentration": conc,
                "n": n,
                "bias_pct": bias,
                "cv_pct": cv,
            }
        )

    summary_df = pd.DataFrame(summary_rows).set_index("concentration")

    # Determine edge levels (LLOQ and ULOQ)
    edge_levels = {summary_df.index.min(), summary_df.index.max()}
    summary_df["is_edge"] = summary_df.index.isin(edge_levels)

    # Accuracy check
    summary_df["bias_ok"] = summary_df.apply(
        lambda r: r["bias_pct"]
        <= (spec.acc_tol_pct_edge if r["is_edge"] else spec.acc_tol_pct_mid),
        axis=1,
    )

    # Precision check
    summary_df["cv_ok"] = summary_df.apply(
        lambda r: r["cv_pct"]
        <= (spec.cv_tol_pct_edge if r["is_edge"] else spec.cv_tol_pct_mid),
        axis=1,
    )

    summary_df["pass"] = summary_df["bias_ok"] & summary_df["cv_ok"]

    n_levels = len(summary_df)
    n_pass = int(summary_df["pass"].sum())
    frac_pass = n_pass / n_levels if n_levels else 0.0

    overall_pass = n_levels >= spec.min_levels and frac_pass >= spec.pass_fraction

    return {
        "num_levels": n_levels,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "per_level": summary_df[
            ["bias_pct", "cv_pct", "is_edge", "bias_ok", "cv_ok", "pass"]
        ].to_dict(orient="index"),
        "pass": overall_pass,
    }
