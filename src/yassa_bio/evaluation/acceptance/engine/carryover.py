from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.carryover import CarryoverSpec
from yassa_bio.schema.layout.enum import SampleType
import pandas as pd


@register("acceptance", CarryoverSpec.__name__)
def eval_carryover(ctx: LBAContext, spec: CarryoverSpec) -> dict:
    df = ctx.data.copy()

    # Ensure required well patterns exist
    missing = [p for p in spec.required_well_patterns if not p.present(df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required blank(s) for carryover",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    # Get LLOQ reference signal from calibration
    cal_df = ctx.calib_df
    lloq_conc = cal_df["concentration"].min()
    lloq_signal = cal_df[cal_df["concentration"] == lloq_conc]["signal"].mean()
    if lloq_signal == 0 or pd.isna(lloq_signal):
        return {"error": "Invalid LLOQ signal (0 or NaN)", "pass": False}

    # Find carryover blank wells
    carry_blanks = df[
        (df["sample_type"] == SampleType.BLANK.value) & (df["carryover"])
    ].copy()

    n_blanks = len(carry_blanks)
    if n_blanks < spec.min_blanks_after_uloq:
        return {
            "error": (
                f"Only {n_blanks} carryover blank(s) found; "
                "expected ≥ {spec.min_blanks_after_uloq}"
            ),
            "pass": False,
        }

    carry_blanks["pct_of_lloq"] = carry_blanks["signal"] / lloq_signal * 100.0
    carry_blanks["pass"] = carry_blanks["pct_of_lloq"] < spec.blank_thresh_pct_lloq

    n_pass = int(carry_blanks["pass"].sum())
    frac_pass = n_pass / n_blanks if n_blanks else 0.0
    overall = frac_pass >= spec.pass_fraction

    return {
        "n_blanks": n_blanks,
        "n_pass": n_pass,
        "pass_fraction": frac_pass,
        "threshold_pct": spec.blank_thresh_pct_lloq,
        "per_blank": carry_blanks[["well", "signal", "pct_of_lloq", "pass"]].to_dict(
            orient="records"
        ),
        "pass": overall,
    }
