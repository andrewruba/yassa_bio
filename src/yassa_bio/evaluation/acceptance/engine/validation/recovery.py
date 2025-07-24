from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.recovery import RecoverySpec
from yassa_bio.schema.layout.enum import RecoveryStage, SampleType
import pandas as pd


@register("acceptance", RecoverySpec.__name__)
def eval_recovery(ctx: LBAContext, spec: RecoverySpec) -> dict:
    df = ctx.data.copy()

    # Validate required well patterns
    missing = [p for p in spec.required_well_patterns if not p.present(df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required recovery pattern(s)",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    # Focus on recovery wells only
    recovery_df = df[
        (df["sample_type"] == SampleType.QUALITY_CONTROL.value)
        & df["recovery_stage"].notna()
    ].copy()

    if recovery_df.empty:
        return {"error": "No recovery wells found", "pass": False}

    recovery_df["back_calc"] = ctx.curve_back(recovery_df["y"].to_numpy(float))

    # Group by QC level
    levels = recovery_df["qc_level"].dropna().unique()
    per_level = {}
    mean_recoveries = {}

    for level in levels:
        sub = recovery_df[recovery_df["qc_level"] == level]
        before = sub[sub["recovery_stage"] == RecoveryStage.BEFORE.value]
        after = sub[sub["recovery_stage"] == RecoveryStage.AFTER.value]

        n_before = len(before)
        n_after = len(after)

        if n_before < spec.min_replicates_each or n_after < spec.min_replicates_each:
            per_level[level] = {
                "n_before": n_before,
                "n_after": n_after,
                "error": f"Fewer than {spec.min_replicates_each} replicates at {level}",
                "pass": False,
            }
            continue

        # Pair-wise match: all AFTERs to mean BEFORE
        before_mean = before["back_calc"].mean()
        after_vals = after["back_calc"]
        recoveries = (
            after_vals / before_mean * 100.0 if before_mean else pd.Series(dtype=float)
        )

        mean_rec = recoveries.mean()
        cv_rec = recoveries.std(ddof=1) / mean_rec * 100.0 if mean_rec else 0.0
        mean_recoveries[level] = mean_rec

        cv_ok = cv_rec <= spec.max_cv_pct_within_level
        per_level[level] = {
            "n_before": n_before,
            "n_after": n_after,
            "mean_recovery": mean_rec,
            "cv_recovery": cv_rec,
            "cv_limit": spec.max_cv_pct_within_level,
            "cv_ok": cv_ok,
            "pass": cv_ok,
        }

    # Check pairwise differences between levels
    between_level_ok = True
    diff_pairs = []
    levels_sorted = sorted(mean_recoveries.keys())

    for i, level_i in enumerate(levels_sorted):
        for level_j in levels_sorted[i + 1 :]:
            rec_i = mean_recoveries[level_i]
            rec_j = mean_recoveries[level_j]
            diff = abs(rec_i - rec_j)
            diff_ok = diff <= spec.max_diff_pct_between_levels
            diff_pairs.append(
                {
                    "pair": f"{level_i} vs {level_j}",
                    "abs_diff": diff,
                    "limit": spec.max_diff_pct_between_levels,
                    "pass": diff_ok,
                }
            )
            if not diff_ok:
                between_level_ok = False

    all_cv_ok = all(v.get("pass", False) for v in per_level.values())
    overall = all_cv_ok and between_level_ok

    return {
        "per_level": per_level,
        "mean_recoveries": mean_recoveries,
        "between_level_differences": diff_pairs,
        "cv_limit": spec.max_cv_pct_within_level,
        "between_level_limit": spec.max_diff_pct_between_levels,
        "pass": overall,
    }
