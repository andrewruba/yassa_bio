from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.stability import StabilitySpec
from yassa_bio.schema.layout.enum import StabilityConditionTime
from yassa_bio.evaluation.acceptance.engine.utils import (
    check_required_well_patterns,
    pattern_error_dict,
    compute_relative_pct_scalar,
)


@register("acceptance", StabilitySpec.__name__)
def eval_stability(ctx: LBAContext, spec: StabilitySpec) -> dict:
    df = ctx.data.copy()

    # Ensure required well patterns exist
    missing = check_required_well_patterns(df, spec.required_well_patterns)
    if missing:
        return pattern_error_dict(
            missing, "Missing {n} required stability QC pattern(s)"
        )

    # Filter rows that match any of the required patterns
    mask = False
    for pat in spec.required_well_patterns:
        mask |= pat.mask(df)
    df = df[mask].copy()

    # Back-calculate
    df["back_calc"] = ctx.curve_back(df["y"].to_numpy(float))

    results = {}
    passed_pairs = 0
    seen_conditions = set()

    grouped = df.groupby(["stability_condition", "qc_level"])

    for (cond, level), sub in grouped:
        seen_conditions.add(cond)

        before = sub[sub["stability_condition_time"] == StabilityConditionTime.BEFORE]
        after = sub[sub["stability_condition_time"] == StabilityConditionTime.AFTER]

        if before.empty or after.empty:
            results[(cond, level)] = {
                "error": "Missing BEFORE or AFTER wells",
                "pass": False,
            }
            continue

        mean_before = before["back_calc"].mean()
        mean_after = after["back_calc"].mean()

        if mean_before == 0:
            results[(cond, level)] = {
                "error": "Zero mean in BEFORE group (cannot compute bias)",
                "pass": False,
            }
            continue

        bias_pct = compute_relative_pct_scalar(
            abs(mean_after - mean_before), mean_before
        )
        bias_ok = bias_pct is not None and bias_pct <= spec.acc_tol_pct

        if bias_ok:
            passed_pairs += 1

        results[(cond, level)] = {
            "n_before": len(before),
            "n_after": len(after),
            "mean_before": mean_before,
            "mean_after": mean_after,
            "bias_pct": bias_pct,
            "pass": bias_ok,
        }

    n_conditions = len(seen_conditions)
    n_total_pairs = len(results)
    frac_pass = passed_pairs / n_total_pairs if n_total_pairs else 0.0
    overall = n_conditions >= spec.min_conditions and frac_pass == 1.0

    return {
        "num_conditions": n_conditions,
        "num_condition_level_pairs": n_total_pairs,
        "pass_fraction": frac_pass,
        "per_condition": {
            f"{cond}/{level}": res for (cond, level), res in results.items()
        },
        "pass": overall,
    }
