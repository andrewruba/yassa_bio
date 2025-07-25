from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.dilution import (
    ValidationDilutionLinearitySpec,
)
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_scalar,
    get_calibration_concentration_for_level,
)


@register("acceptance", ValidationDilutionLinearitySpec.__name__)
def eval_dilution_linearity(
    ctx: LBAContext, spec: ValidationDilutionLinearitySpec
) -> dict:
    df = ctx.data.copy()

    # Ensure required well patterns are present
    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(missing, "Missing {n} required dilution pattern(s)")

    df["back_calc"] = ctx.curve_back(df["y"].to_numpy(float))

    # Evaluate dilution linearity by level_idx
    in_range_qc = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (
            df["qc_level"].isin(
                [
                    QCLevel.LLOQ,
                    QCLevel.LOW,
                    QCLevel.MID,
                    QCLevel.HIGH,
                    QCLevel.ULOQ,
                ]
            )
        )
    ]
    grouped = in_range_qc.groupby("level_idx")
    point_results = []

    for level, sub in grouped:
        n = len(sub)
        if n < spec.min_replicates:
            point_results.append(
                {
                    "level_idx": level,
                    "n": n,
                    "error": (
                        f"Only {n} replicates (min required: {spec.min_replicates})"
                    ),
                    "pass": False,
                }
            )
            continue

        expected = sub["x"].mean()
        observed = sub["back_calc"].mean()
        acc_pct = compute_relative_pct_scalar(abs(observed - expected), expected) or 0.0
        cv = sub["back_calc"].std(ddof=1) / observed * 100.0 if observed else 0.0

        acc_ok = acc_pct <= spec.acc_tol_pct
        cv_ok = cv <= spec.cv_tol_pct
        point_pass = acc_ok and cv_ok

        point_results.append(
            {
                "level_idx": level,
                "n": n,
                "acc_pct": acc_pct,
                "cv_pct": cv,
                "acc_ok": acc_ok,
                "cv_ok": cv_ok,
                "pass": point_pass,
            }
        )

    # Hook effect check
    hook_results = []
    hook_failures = 0
    uloq_conc = get_calibration_concentration_for_level(ctx.calib_df, QCLevel.ULOQ)

    above_uloq_qc = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL)
        & (df["qc_level"] == QCLevel.ABOVE_ULOQ)
    ]

    for idx, row in above_uloq_qc.iterrows():
        recovery = compute_relative_pct_scalar(row["back_calc"], row["x"])
        above_uloq = row["back_calc"] > uloq_conc
        sufficient_recovery = (
            recovery is not None and recovery >= spec.undiluted_recovery_min_pct
        )
        hook_ok = above_uloq and sufficient_recovery

        hook_results.append(
            {
                "well": row.get("well", f"row_{idx}"),
                "x": row["x"],
                "back_calc": row["back_calc"],
                "recovery_pct": recovery,
                "uloq_conc": uloq_conc,
                "above_uloq": above_uloq,
                "recovery_ok": sufficient_recovery,
                "hook_ok": hook_ok,
            }
        )

        if not hook_ok:
            hook_failures += 1

    # Pass logic
    n_total = len(point_results)
    n_pass = sum(1 for r in point_results if r["pass"])
    distinct_levels = df["level_idx"].nunique()

    pass_conditions = [
        distinct_levels >= spec.min_dilutions,
        all(r["pass"] for r in point_results),
        hook_failures == 0,
    ]

    return {
        "num_dilution_levels": distinct_levels,
        "n_total_points": n_total,
        "n_pass": n_pass,
        "hook_failures": hook_failures,
        "per_point": point_results,
        "hook_checks": hook_results,
        "pass": all(pass_conditions),
    }
