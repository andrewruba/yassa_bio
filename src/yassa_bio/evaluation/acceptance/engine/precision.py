from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.precision import PrecisionSpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


@register("acceptance", PrecisionSpec.__name__)
def eval_precision(ctx: LBAContext, spec: PrecisionSpec) -> dict:
    df = ctx.data.copy()
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL.value].copy()

    if "qc_level" not in qc_df.columns:
        return {"error": "Missing 'qc_level' column in QC data", "pass": False}

    # Check presence of required well patterns
    missing = [p for p in spec.required_well_patterns if not p.present(qc_df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required QC pattern(s)",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    # Back-calculate concentrations
    qc_df["back_calc"] = ctx.curve_back(qc_df["y"].to_numpy(float))
    qc_df["bias_pct"] = ((qc_df["back_calc"] - qc_df["x"]) / qc_df["x"]).abs() * 100.0

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

        back = level_df["back_calc"]
        mean_back = back.mean()
        cv = back.std(ddof=1) / mean_back * 100.0 if mean_back else 0.0
        bias = level_df["bias_pct"].mean()
        total_error = cv + bias

        is_edge = pat.qc_level in {QCLevel.LLOQ, QCLevel.ULOQ}
        cv_tol = spec.cv_tol_pct_edge if is_edge else spec.cv_tol_pct_mid
        total_tol = spec.total_error_pct_edge if is_edge else spec.total_error_pct_mid

        cv_ok = cv <= cv_tol
        total_ok = total_error <= total_tol
        level_pass = cv_ok and total_ok

        if level_pass:
            passed_levels += 1

        per_level[pat.qc_level] = {
            "n": n,
            "cv_pct": cv,
            "bias_pct": bias,
            "total_error_pct": total_error,
            "cv_tol": cv_tol,
            "total_tol": total_tol,
            "cv_ok": cv_ok,
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
