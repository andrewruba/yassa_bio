# yassa_bio/pipeline/run_plate.py
from __future__ import annotations

import pandas as pd

from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.analysis.steps.preprocessing import preprocess_df  # new helper
from yassa_bio.analysis.registry import registry  # plug-in map


def run_plate(plate_df: pd.DataFrame, cfg: LBAAnalysisConfig):
    """
    Execute the complete analytic workflow on *one* plate’s tidy DataFrame.

    Parameters
    ----------
    plate_df : tidy DataFrame
        Must contain at least: plate_id, sample_type, level_idx, signal_raw …
        (anything your Preprocess / curve-fit stages expect).
    cfg : LBAAnalysisConfig
        User-supplied analysis settings (preprocess & curve_fit blocks).

    Returns
    -------
    results : dict
        Whatever you want to bubble upward: model params, QC stats, etc.
    """

    # ------------------------------------------------------------------ #
    # 1 ─── Pre-processing                                               #
    # ------------------------------------------------------------------ #
    prep_res = preprocess_df(plate_df, cfg.preprocess)  # ← new call

    # Throw out wells flagged as outliers / excluded by template
    work = prep_res.df.loc[~prep_res.df.is_outlier & ~prep_res.df.exclude].copy()

    # ------------------------------------------------------------------ #
    # 2 ─── Build weighting + transforms                                 #
    # ------------------------------------------------------------------ #
    fit_cfg = cfg.curve_fit

    model_cls = registry.get("curve_model", fit_cfg.model)  # 4PL / 5PL / linear

    model = model_cls(
        x_transform=registry.get("transform", fit_cfg.transformation_x),
        y_transform=registry.get("transform", fit_cfg.transformation_y),
        weighting=registry.get("weighting", fit_cfg.weighting),
    )

    # Identify the calibration-standard wells
    std_mask = work["sample_type"] == "calibration_standard"
    std_x = work.loc[
        std_mask, "concentration_nominal"
    ]  # you may call it something else
    std_y = work.loc[std_mask, "clean_signal"]

    # Optional: weight column already computed in preprocess_df, or build here
    std_w = work.loc[std_mask, "weight"] if "weight" in work else None

    # ------------------------------------------------------------------ #
    # 3 ─── Fit the curve                                                #
    # ------------------------------------------------------------------ #
    model.fit(std_x.to_numpy(), std_y.to_numpy(), std_w)

    # ------------------------------------------------------------------ #
    # 4 ─── Down-stream steps (back-calc samples, QC stats, reports)     #
    # ------------------------------------------------------------------ #
    # … e.g.,
    # work["conc_calc"] = model.back_calc(work["clean_signal"])
    # qc_stats = qc_engine.evaluate(work, model, cfg.acceptance)

    return {
        "prep": prep_res,  # blank value, norm span, outlier mask
        "model": model,  # fitted instance with params + r²
        # "qc"  : qc_stats,
        # "data": work           # maybe return the clean dataframe
    }
