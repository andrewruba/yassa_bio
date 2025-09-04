from __future__ import annotations

from yassa_bio.core.registry import get
from yassa_bio.pipeline.base import Step
from yassa_bio.pipeline.composite import CompositeStep
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.analysis.enum import CurveModel
from yassa_bio.schema.layout.enum import SampleType


class ApplyTransforms(Step):
    name = "apply_transforms"
    fingerprint_keys = (
        "data",
        "analysis_config",
    )

    def logic(self, ctx: LBAContext) -> LBAContext:
        cfg: LBAAnalysisConfig = ctx.analysis_config
        tf_x = get("transform", cfg.curve_fit.transformation_x)
        tf_y = get("transform", cfg.curve_fit.transformation_y)

        df = ctx.data.copy()
        df["x"] = tf_x(df["concentration"].to_numpy(float))
        df["y"] = tf_y(df["signal"].to_numpy(float))

        ctx.data = df
        return ctx


class ComputeWeights(Step):
    name = "compute_weights"
    fingerprint_keys = (
        "data",
        "analysis_config",
    )

    def logic(self, ctx: LBAContext) -> LBAContext:
        cfg: LBAAnalysisConfig = ctx.analysis_config
        wt_fn = get("weighting", cfg.curve_fit.weighting)

        df = ctx.data.copy()
        x = df["x"].to_numpy(float)
        y = df["y"].to_numpy(float)

        df["w"] = wt_fn(x, y)

        ctx.data = df
        return ctx


class SelectCalibrationData(Step):
    name = "select_calibration"
    fingerprint_keys = ("data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        df = ctx.data
        cal_df = df[df["sample_type"] == SampleType.CALIBRATION_STANDARD.value].copy()
        if cal_df.empty:
            raise ValueError("No calibration-standard wells found in ctx.data")
        ctx.calib_df = cal_df
        return ctx


class FitCalibrationData(Step):
    name = "fit_calibration_data"
    fingerprint_keys = (
        "calib_df",
        "analysis_config",
    )

    def logic(self, ctx: LBAContext) -> LBAContext:
        cfg: LBAAnalysisConfig = ctx.analysis_config
        model: CurveModel = cfg.curve_fit.model

        fit_fn = get("curve_model", model)
        back_fn = get("curve_model_back", model)

        x = ctx.calib_df["x"].to_numpy(float)
        y = ctx.calib_df["y"].to_numpy(float)
        w = ctx.calib_df["w"].to_numpy(float)

        fwd_func, params = fit_fn(x, y, weights=w)

        ctx.curve_fwd = fwd_func
        ctx.curve_back = lambda y_val: back_fn(y_val, params)
        ctx.curve_params = params
        return ctx


class CurveFit(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="curve_fit",
            children=[
                ApplyTransforms(),
                ComputeWeights(),
                SelectCalibrationData(),
                FitCalibrationData(),
            ],
        )
