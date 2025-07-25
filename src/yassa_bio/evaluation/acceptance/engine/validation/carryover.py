from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.carryover import ValidationCarryoverSpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    get_calibration_signal_for_level,
)
import pandas as pd


@register("acceptance", ValidationCarryoverSpec.__name__)
def eval_carryover(ctx: LBAContext, spec: ValidationCarryoverSpec) -> dict:
    df = ctx.data.copy()

    # Ensure required well patterns exist
    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(
            missing, "Missing {n} required blank(s) for carryover"
        )

    # Get LLOQ signal from calibration
    lloq_signal = get_calibration_signal_for_level(ctx.calib_df, QCLevel.LLOQ)
    if not lloq_signal or pd.isna(lloq_signal):
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
                f"expected ≥ {spec.min_blanks_after_uloq}"
            ),
            "pass": False,
        }

    carry_blanks["pass"] = carry_blanks["signal"] < lloq_signal

    n_pass = int(carry_blanks["pass"].sum())
    overall = n_pass == n_blanks

    return {
        "n_blanks": n_blanks,
        "n_pass": n_pass,
        "lloq_signal": lloq_signal,
        "per_blank": carry_blanks[["well", "signal", "pass"]].to_dict(orient="records"),
        "pass": overall,
    }
