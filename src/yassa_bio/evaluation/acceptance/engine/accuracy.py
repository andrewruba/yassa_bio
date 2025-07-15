from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.accuracy import AccuracySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


@register("acceptance", AccuracySpec.__name__)
def eval_accuracy(ctx: LBAContext, spec: AccuracySpec) -> dict:
    df = ctx.data.copy()
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL.value].copy()

    if "qc_level" not in qc_df.columns:
        return {"error": "Missing 'qc_level' column in QC data", "pass": False}

    # Ensure required well patterns are present
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

        # Calculate accuracy and precision
        mean_nominal = level_df["x"].mean()
        mean_back = level_df["back_calc"].mean()
        bias = abs(mean_back - mean_nominal) / mean_nominal * 100.0
        cv = level_df["back_calc"].std(ddof=1) / mean_back * 100.0 if mean_back else 0.0
        total_error = bias + cv

        is_edge = pat.qc_level in {QCLevel.LLOQ, QCLevel.ULOQ}
        bias_tol = spec.acc_tol_pct_edge if is_edge else spec.acc_tol_pct_mid
        total_tol = spec.total_error_pct_edge if is_edge else spec.total_error_pct_mid

        bias_ok = bias <= bias_tol
        total_ok = total_error <= total_tol
        level_pass = bias_ok and total_ok

        if level_pass:
            passed_levels += 1

        per_level[pat.qc_level] = {
            "n": n,
            "bias_pct": bias,
            "cv_pct": cv,
            "total_error_pct": total_error,
            "bias_tol": bias_tol,
            "total_tol": total_tol,
            "bias_ok": bias_ok,
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
