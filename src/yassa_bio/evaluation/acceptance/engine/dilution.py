from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.dilution import DilutionLinearitySpec


@register("acceptance", DilutionLinearitySpec.__name__)
def eval_dilution_linearity(ctx: LBAContext, spec: DilutionLinearitySpec) -> dict:
    df = ctx.data.copy()

    required_cols = {"dilution_factor", "series_id", "back_calc", "x"}
    if not required_cols.issubset(df.columns):
        return {
            "error": (
                f"Missing required columns: {sorted(required_cols - set(df.columns))}"
            ),
            "pass": False,
        }

    # Group by (dilution_factor, series_id)
    grouped = df.groupby(["dilution_factor", "series_id"])
    point_results = []
    hook_results = []

    for (factor, series), sub in grouped:
        n = len(sub)
        if n < spec.min_replicates_per_point:
            point_results.append(
                {
                    "dilution_factor": factor,
                    "series_id": series,
                    "n": n,
                    "error": (
                        f"Only {n} replicates (min required: {spec.min_replicates})"
                    ),
                    "pass": False,
                }
            )
            continue

        # Accuracy
        expected = sub["x"].mean() / factor  # Expected after dilution
        observed = sub["back_calc"].mean()
        bias_pct = abs(observed - expected) / expected * 100.0 if expected else 0.0

        # Precision
        cv = sub["back_calc"].std(ddof=1) / observed * 100.0 if observed else 0.0
        bias_ok = bias_pct <= spec.acc_tol_pct
        cv_ok = cv <= spec.cv_tol_pct
        passed = bias_ok and cv_ok

        point_results.append(
            {
                "dilution_factor": factor,
                "series_id": series,
                "n": n,
                "bias_pct": bias_pct,
                "cv_pct": cv,
                "bias_ok": bias_ok,
                "cv_ok": cv_ok,
                "pass": passed,
            }
        )

    # Check distinct dilution factors and series counts
    # dilution_counts = df["dilution_factor"].value_counts()
    distinct_factors = df["dilution_factor"].nunique()
    series_counts = df.groupby("dilution_factor")["series_id"].nunique().to_dict()

    # Hook effect check
    hook_failures = 0
    hook_checked = 0
    diluted = df[df["dilution_factor"] > 1].copy()
    undiluted = df[df["dilution_factor"] == 1]

    if not undiluted.empty:
        ref = undiluted["back_calc"].mean()
        for factor, series in diluted.groupby(["dilution_factor", "series_id"]):
            expected = series["back_calc"].mean()
            if expected > 0:
                recovery = ref / expected * 100.0
                hook_checked += 1
                if recovery < spec.undiluted_recovery_min_pct:
                    hook_failures += 1
                hook_results.append(
                    {
                        "recovery_pct": recovery,
                        "factor": factor,
                        "hook_ok": recovery >= spec.undiluted_recovery_min_pct,
                    }
                )

    # Pass logic
    n_total = len(point_results)
    n_pass = sum(1 for p in point_results if p["pass"])
    frac_pass = n_pass / n_total if n_total else 0.0

    pass_conditions = [
        distinct_factors >= spec.min_dilution_factors,
        all(series_counts.get(f, 0) >= spec.min_series for f in series_counts),
        frac_pass >= spec.pass_fraction,
        hook_failures == 0,
    ]
    overall = all(pass_conditions)

    return {
        "num_dilution_factors": distinct_factors,
        "series_counts_per_factor": series_counts,
        "n_total_points": n_total,
        "n_pass": n_pass,
        "pass_fraction": frac_pass,
        "min_series": spec.min_series,
        "min_dilution_factors": spec.min_dilution_factors,
        "hook_failures": hook_failures,
        "undiluted_recovery_min_pct": spec.undiluted_recovery_min_pct,
        "per_point": point_results,
        "hook_checks": hook_results,
        "pass": overall,
    }
