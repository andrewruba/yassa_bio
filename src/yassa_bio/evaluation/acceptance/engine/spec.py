from __future__ import annotations
import pandas as pd
from collections import defaultdict

from yassa_bio.core.registry import register
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical import (
    AnalyticalCalibrationSpec,
    AnalyticalQCSpec,
)
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import (
    SampleType,
    QCLevel,
)


@register("acceptance_rule", AnalyticalCalibrationSpec.__name__)
def eval_calibration(ctx: LBAContext, spec: AnalyticalCalibrationSpec) -> dict:
    cal = ctx.calib_df.copy()
    by_lvl = cal.groupby("concentration")
    cal["back_calc"] = ctx.curve_back(cal["y"].to_numpy(float))

    summary = by_lvl.apply(
        lambda g: pd.Series(
            {
                "nominal": g["concentration"].mean(),
                "back_mean": g["back_calc"].mean(),
            }
        )
    )

    summary["bias_pct"] = (
        (summary["back_mean"] - summary["nominal"]).abs() / summary["nominal"] * 100.0
    )

    edge_levels = {summary.index.min(), summary.index.max()}
    summary["is_edge"] = summary.index.isin(edge_levels)

    tol_mid, tol_edge = spec.acc_tol_pct_mid, spec.acc_tol_pct_edge
    summary["pass"] = summary.apply(
        lambda r: r["bias_pct"] <= (tol_edge if r["is_edge"] else tol_mid), axis=1
    )

    n_levels = len(summary)
    n_pass = int(summary["pass"].sum())
    frac_pass = n_pass / n_levels if n_levels else 0.0

    failing_levels = summary[~summary["pass"]].index
    n_fail = len(failing_levels)
    n_retained = n_levels - n_fail

    can_refit = n_retained >= spec.min_retained_levels

    overall_pass = (
        can_refit and frac_pass >= spec.pass_fraction and n_levels >= spec.min_levels
    )

    return {
        "num_levels": n_levels,
        "num_pass": n_pass,
        "pass_fraction": frac_pass,
        "failing_levels": failing_levels.tolist(),
        "per_level": summary[["bias_pct", "pass"]].to_dict(orient="index"),
        "can_refit": can_refit,
        "pass": overall_pass,
    }


@register("acceptance_rule", AnalyticalQCSpec.__name__)
def eval_qc(ctx: LBAContext, spec: AnalyticalQCSpec) -> dict:
    """
    Evaluate QC-well accuracy/precision for an analytical run.

    ── Algorithm ───────────────────────────────────────────────────────────
    1.  Verify that every RequiredWellPattern is represented at least once.
    2.  Back-calculate concentrations for all QC wells (if not already done).
    3.  Compute per-well %-bias and PASS/FAIL vs `qc_tol_pct`.
    4.  Aggregate:
        • total pass fraction across *all* QC wells
        • per-level (LOW / MID / HIGH) pass fractions
    5.  Decide overall PASS/FAIL per ICH M10 rules
        – `pass_fraction_total`
        – `pass_fraction_each_level`
    6.  Return a rich dict that mirrors the structure used in
        `eval_calibration`.
    """
    # ── 0.  Pull out the QC rows ──────────────────────────────────────────
    df = ctx.data
    qc_df = df[df["sample_type"] == SampleType.QUALITY_CONTROL.value].copy()

    # ── 1.  Pattern-presence check ────────────────────────────────────────
    wells = [
        WellTemplate.model_validate(rec, strict=False)
        for rec in qc_df.to_dict("records")
    ]

    missing_patterns = [
        pat
        for pat in spec.required_well_patterns
        if not any(pat.matches(w) for w in wells)
    ]
    if missing_patterns:
        return {
            "error": f"Missing {len(missing_patterns)} required QC pattern(s)",
            "missing_patterns": [p.dict() for p in missing_patterns],
            "pass": False,
        }

    # ── 2.  Back-calc & per-well bias ─────────────────────────────────────
    if "back_calc" not in qc_df.columns:
        qc_df["back_calc"] = ctx.curve_back(qc_df["signal"].to_numpy(float))

    qc_df["bias_pct"] = (
        (qc_df["back_calc"] - qc_df["concentration"]).abs()
        / qc_df["concentration"]
        * 100.0
    )
    qc_df["pass"] = qc_df["bias_pct"] <= spec.qc_tol_pct

    # ── 3.  Totals ────────────────────────────────────────────────────────
    n_total = len(qc_df)
    n_pass_total = int(qc_df["pass"].sum())
    frac_pass_total = n_pass_total / n_total if n_total else 0.0

    # ── 4.  Per-level stats ──────────────────────────────────────────────
    per_level: dict[str, dict] = defaultdict(dict)
    failing_wells: list[int] = []  # row indices of failed wells

    for lvl in (QCLevel.LOW, QCLevel.MID, QCLevel.HIGH):
        sub = qc_df[qc_df["qc_level"] == lvl.value]
        n_lvl = len(sub)
        n_pass_lvl = int(sub["pass"].sum())
        frac_pass_lvl = n_pass_lvl / n_lvl if n_lvl else 0.0

        per_level[lvl.value].update(
            {
                "n": n_lvl,
                "num_pass": n_pass_lvl,
                "pass_frac": frac_pass_lvl,
                "pass": frac_pass_lvl >= spec.pass_fraction_each_level,
            }
        )

        failing_wells.extend(sub[~sub["pass"]].index.tolist())

    # ── 5.  Overall decision ─────────────────────────────────────────────
    overall_pass = frac_pass_total >= spec.pass_fraction_total and all(
        d["pass"] for d in per_level.values()
    )

    # ── 6.  Return payload mirroring eval_calibration ────────────────────
    return {
        "total_wells": n_total,
        "num_pass": n_pass_total,
        "pass_fraction": frac_pass_total,
        "per_level": per_level,  # {LOW: {…}, MID: {…}, HIGH: {…}}
        "failing_wells": failing_wells,  # Data-frame indices for traceability
        "pass": overall_pass,
    }
