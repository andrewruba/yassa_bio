from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.stability import StabilitySpec
from yassa_bio.schema.layout.enum import SampleType, StabilityConditionTime


@register("acceptance", StabilitySpec.__name__)
def eval_stability(ctx: LBAContext, spec: StabilitySpec) -> dict:
    df = ctx.data.copy()
    df = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL.value)
        & df["stability_condition"].notna()
        & df["stability_condition_time"].notna()
    ].copy()

    if df.empty:
        return {
            "error": "No QC wells with stability condition annotations found.",
            "pass": False,
        }

    # Validate required patterns
    missing = [p for p in spec.required_well_patterns if not p.present(ctx.data)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required stability QC pattern(s)",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    df["back_calc"] = ctx.curve_back(df["y"].to_numpy(float))

    grouped = df.groupby(["stability_condition", "qc_level"])
    results = {}
    n_conditions_passed = 0
    seen_conditions = set()

    for (cond, level), sub in grouped:
        seen_conditions.add(cond)

        if cond is None or level is None:
            continue

        sub_before = sub[
            sub["stability_condition_time"] == StabilityConditionTime.BEFORE
        ]
        sub_after = sub[sub["stability_condition_time"] == StabilityConditionTime.AFTER]

        if sub_before.empty or sub_after.empty:
            results[(cond, level)] = {
                "error": "Missing BEFORE or AFTER wells",
                "pass": False,
            }
            continue

        mean_before = sub_before["back_calc"].mean()
        mean_after = sub_after["back_calc"].mean()

        if mean_before == 0:
            results[(cond, level)] = {
                "error": "Zero mean in BEFORE group (cannot compute bias)",
                "pass": False,
            }
            continue

        bias_pct = abs(mean_after - mean_before) / mean_before * 100.0
        pass_bias = bias_pct <= spec.acc_tol_pct

        if pass_bias:
            n_conditions_passed += 1

        results[(cond, level)] = {
            "n_before": len(sub_before),
            "n_after": len(sub_after),
            "mean_before": mean_before,
            "mean_after": mean_after,
            "bias_pct": bias_pct,
            "acc_tol_pct": spec.acc_tol_pct,
            "pass": pass_bias,
        }

    n_conditions = len(seen_conditions)
    n_condition_level_pairs = len(results)
    frac_pass = (
        sum(1 for r in results.values() if r["pass"]) / n_condition_level_pairs
        if n_condition_level_pairs
        else 0.0
    )

    overall = n_conditions >= spec.min_conditions and frac_pass >= spec.pass_fraction

    return {
        "num_conditions": n_conditions,
        "num_condition_level_pairs": n_condition_level_pairs,
        "pass_fraction": frac_pass,
        "required_fraction": spec.pass_fraction,
        "acc_tol_pct": spec.acc_tol_pct,
        "per_condition": {
            f"{cond}/{level}": res for (cond, level), res in results.items()
        },
        "pass": overall,
    }
