import pandas as pd

from yassa_bio.core.registry import get
from yassa_bio.pipeline.base import Step, PipelineContext
from yassa_bio.pipeline.composite import CompositeStep


class LoadData(Step):
    name = "load_data"
    fingerprint_keys = ()

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        # TODO: load data from batch files and templates.
        return ctx


class CheckData(Step):
    name = "check_data"
    fingerprint_keys = ()

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        # TODO: add shape / column checks etc.
        # check signal column
        # check run_type is present
        return ctx


class SubtractBlank(Step):
    name = "subtract_blank"
    fingerprint_keys = ("data",)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        df: pd.DataFrame = ctx.data
        cfg = ctx.config
        sig = "signal"

        blank_mask = df["sample_type"].eq("blank")
        blank_fn = get("blank_rule", cfg.blank_rule)

        blank_val = blank_fn(df[sig].to_numpy(float), blank_mask.to_numpy())
        clean = df[sig].astype(float)
        if blank_val is not None:
            clean -= blank_val

        df["signal_bs"] = clean
        ctx.blank_used = blank_val
        ctx.data = df
        return ctx


class NormalizeSignal(Step):
    name = "normalize_signal"
    fingerprint_keys = ("data",)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        df, cfg = ctx.data, ctx.config
        norm_fn = get("norm_rule", cfg.norm_rule)

        clean, span = norm_fn(df.assign(signal=df["signal_bs"]))
        df["clean_signal"] = clean

        ctx.norm_span = span
        ctx.data = df
        return ctx


class MaskOutliers(Step):
    name = "mask_outliers"
    fingerprint_keys = ("data",)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        df, cfg = ctx.data, ctx.config
        out_fn = get("outlier_rule", cfg.outliers.rule)

        df["is_outlier"] = out_fn(df["clean_signal"].to_numpy(float), cfg.outliers)
        ctx.data = df
        return ctx


class Preprocess(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="preprocess",
            children=[
                LoadData(),
                CheckData(),
                SubtractBlank(),
                NormalizeSignal(),
                MaskOutliers(),
            ],
        )
