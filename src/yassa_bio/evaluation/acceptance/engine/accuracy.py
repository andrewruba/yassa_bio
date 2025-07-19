from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.accuracy import AccuracySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_vectorized,
)


@register("acceptance", AccuracySpec.__name__)
def eval_accuracy(ctx: LBAContext, spec: AccuracySpec) -> dict:
    df = ctx.data.copy()
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL].copy()

    if "qc_level" not in qc_df.columns:
        return {"error": "Missing 'qc_level' column in QC data", "pass": False}

    # Ensure required well patterns are present
    missing = check_required_well_patterns(qc_df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(missing, "Missing {n} required QC pattern(s)")

    # Back-calculate concentrations
    qc_df["back_calc"] = ctx.curve_back(qc_df["y"].to_numpy(float))
    qc_df["acc_pct"] = compute_relative_pct_vectorized(
        (qc_df["back_calc"] - qc_df["x"]).abs(), qc_df["x"]
    )

    per_level = {}
    passed_levels = 0

    for pat in spec.required_well_patterns:
        level_df = qc_df[
            (qc_df["qc_level"] == pat.qc_level)
            & (qc_df["sample_type"] == pat.sample_type)
        ]
        n = len(level_df)

        if n < spec.min_replicates_per_level:
            per_level[pat.qc_level] = {
                "n": n,
                "error": f"Fewer than {spec.min_replicates_per_level} replicates",
                "pass": False,
            }
            continue

        # Calculate mean accuracy and total error
        mean_acc = level_df["acc_pct"].mean()
        total_error = level_df["acc_pct"].sum()

        is_edge = pat.qc_level in {QCLevel.LLOQ, QCLevel.ULOQ}
        acc_tol = spec.acc_tol_pct_edge if is_edge else spec.acc_tol_pct_mid
        total_tol = spec.total_error_pct_edge if is_edge else spec.total_error_pct_mid

        acc_ok = mean_acc <= acc_tol
        total_ok = total_error <= total_tol
        level_pass = acc_ok and total_ok

        if level_pass:
            passed_levels += 1

        per_level[pat.qc_level] = {
            "n": n,
            "mean_acc_pct": mean_acc,
            "total_error_pct": total_error,
            "acc_tol": acc_tol,
            "total_tol": total_tol,
            "acc_ok": acc_ok,
            "total_ok": total_ok,
            "pass": level_pass,
        }

    overall_pass = passed_levels >= spec.min_levels

    return {
        "num_levels": len(per_level),
        "num_pass": passed_levels,
        "min_levels": spec.min_levels,
        "per_level": per_level,
        "pass": overall_pass,
    }
