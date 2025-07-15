from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.validation.selectivity import SelectivitySpec
from yassa_bio.schema.layout.enum import SampleType, QCLevel


@register("acceptance", SelectivitySpec.__name__)
def eval_selectivity(ctx: LBAContext, spec: SelectivitySpec) -> dict:
    df = ctx.data.copy()

    # 1. Required well patterns
    missing = [p for p in spec.required_well_patterns if not p.present(df)]
    if missing:
        return {
            "error": f"Missing {len(missing)} required well pattern(s)",
            "missing_patterns": [p.model_dump() for p in missing],
            "pass": False,
        }

    # 2. Reference signal for blank check — from calibration
    cal = ctx.calib_df
    lloq_conc = cal["concentration"].min()
    lloq_signal = cal[cal["concentration"] == lloq_conc]["signal"].mean()
    if lloq_signal == 0:
        return {"error": "LLOQ calibration signal is 0", "pass": False}

    # 3. Evaluate each source
    source_results = {}
    df["matrix_type"] = df["matrix_type"].fillna("normal")
    grouped = df.groupby("source_id")

    for sid, sub in grouped:
        matrix_type = sub["matrix_type"].iloc[0]
        entry = {"matrix_type": matrix_type}

        # --- Blank: signal < X% of LLOQ
        blank = sub[sub["sample_type"] == SampleType.BLANK]
        blank_mean = blank["signal"].mean()
        blank_pct = blank_mean / lloq_signal * 100.0 if lloq_signal else 0.0
        entry["blank_pct_of_lloq"] = blank_pct
        entry["blank_ok"] = blank_pct < spec.blank_thresh_pct_lloq

        # --- LLOQ QC
        lloq = sub[
            (sub["sample_type"] == SampleType.QUALITY_CONTROL)
            & (sub["qc_level"] == QCLevel.LLOQ)
        ]
        if not lloq.empty:
            lloq_bias = (
                abs((lloq["y"].mean() - lloq["x"].mean()) / lloq["x"].mean()) * 100.0
            )
            entry["lloq_bias_pct"] = lloq_bias
            entry["lloq_ok"] = lloq_bias <= spec.acc_tol_pct_lloq
        else:
            entry["lloq_ok"] = False
            entry["lloq_bias_pct"] = None

        # --- High QC
        high = sub[
            (sub["sample_type"] == SampleType.QUALITY_CONTROL)
            & (sub["qc_level"] == QCLevel.HIGH)
        ]
        if not high.empty:
            high_bias = (
                abs((high["y"].mean() - high["x"].mean()) / high["x"].mean()) * 100.0
            )
            entry["high_bias_pct"] = high_bias
            entry["high_ok"] = high_bias <= spec.acc_tol_pct_high
        else:
            entry["high_ok"] = False
            entry["high_bias_pct"] = None

        entry["pass"] = entry["blank_ok"] and entry["lloq_ok"] and entry["high_ok"]
        source_results[sid] = entry

    # 4. Pass/fail summary
    n_sources = len(source_results)
    n_pass = sum(1 for r in source_results.values() if r["pass"])
    frac_pass = n_pass / n_sources if n_sources else 0.0
    overall_pass = frac_pass >= spec.pass_fraction and n_sources >= spec.min_sources

    # 5. Matrix-type breakdown
    matrix_type_counts: dict[str, int] = {}
    for r in source_results.values():
        t = r["matrix_type"]
        matrix_type_counts[t] = matrix_type_counts.get(t, 0) + 1

    return {
        "num_sources": n_sources,
        "num_passed": n_pass,
        "pass_fraction": frac_pass,
        "matrix_types": matrix_type_counts,
        "per_source": source_results,
        "pass": overall_pass,
    }
