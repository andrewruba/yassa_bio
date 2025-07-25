from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical.parallelism import AnalyticalParallelismSpec
from yassa_bio.schema.layout.enum import SampleType


@register("acceptance", AnalyticalParallelismSpec.__name__)
def eval_parallelism(ctx: LBAContext, spec: AnalyticalParallelismSpec) -> dict:
    df = ctx.data.copy()

    required_cols = {"sample_id", "dilution_factor", "back_calc"}
    if not required_cols.issubset(df.columns):
        return {
            "error": (
                f"Missing required columns: {sorted(required_cols - set(df.columns))}"
            ),
            "pass": False,
        }

    df = df[
        (df["sample_type"] == SampleType.SAMPLE.value)
        & df["sample_id"].notna()
        & df["dilution_factor"].notna()
    ].copy()

    # Check for required well patterns
    missing = [p for p in spec.required_well_patterns if not p.present(df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required sample patterns",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    series_results = []
    grouped = df.groupby("sample_id")

    for sid, sub in grouped:
        dilution_counts = sub["dilution_factor"].value_counts()
        n_dilutions = dilution_counts.nunique()

        if n_dilutions < spec.min_dilutions:
            series_results.append(
                {
                    "sample_id": sid,
                    "n_dilutions": n_dilutions,
                    "error": (
                        f"Only {n_dilutions} dilution(s); "
                        "requires ≥ {spec.min_dilutions}"
                    ),
                    "pass": False,
                }
            )
            continue

        # Check replicates for each dilution
        valid = True
        for factor, count in dilution_counts.items():
            if count < spec.min_replicates_each:
                valid = False
                series_results.append(
                    {
                        "sample_id": sid,
                        "dilution_factor": factor,
                        "error": (
                            f"Only {count} replicates; "
                            "requires ≥ {spec.min_replicates_each}"
                        ),
                        "pass": False,
                    }
                )
                break

        if not valid:
            continue

        # Compute CV across all back-calculated concentrations
        cv = (
            sub["back_calc"].std(ddof=1) / sub["back_calc"].mean() * 100.0
            if sub["back_calc"].mean()
            else 0.0
        )
        passed = cv <= spec.cv_tol_pct

        series_results.append(
            {
                "sample_id": sid,
                "n_dilutions": n_dilutions,
                "cv_pct": cv,
                "cv_tol": spec.cv_tol_pct,
                "pass": passed,
            }
        )

    n_series = len(series_results)
    n_pass = sum(1 for r in series_results if r.get("pass"))
    frac_pass = n_pass / n_series if n_series else 0.0
    overall = frac_pass >= spec.pass_fraction

    return {
        "num_series": n_series,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "required_fraction": spec.pass_fraction,
        "per_series": series_results,
        "pass": overall,
    }
