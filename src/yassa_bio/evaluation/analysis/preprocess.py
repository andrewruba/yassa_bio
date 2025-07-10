import pandas as pd
from typing import Iterable

from yassa_bio.core.registry import get
from yassa_bio.pipeline.base import Step
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.pipeline.composite import CompositeStep


class LoadData(Step):
    name = "load_data"
    fingerprint_keys = ("batch_data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        obj = ctx.batch_data
        if hasattr(obj, "df"):
            ctx.data = obj.df
        else:
            raise TypeError("ctx.batch_data must have a .df property")
        return ctx


class CheckData(Step):
    name = "check_data"
    fingerprint_keys = ("data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        df: pd.DataFrame = ctx.data

        if not isinstance(df, pd.DataFrame):
            raise TypeError("ctx.data must be a pandas DataFrame")

        required = {"signal", "concentration"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if df.empty:
            raise ValueError("DataFrame is empty")

        if not pd.api.types.is_numeric_dtype(df["signal"]):
            raise TypeError("'signal' column must be numeric")

        return ctx


class SubtractBlank(Step):
    name = "subtract_blank"
    fingerprint_keys = ("data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        df: pd.DataFrame = ctx.data
        cfg = ctx.analysis_config

        blank_mask = df["sample_type"].eq("blank")
        blank_fn = get("blank_rule", cfg.blank_rule)

        blank_val = blank_fn(df["signal"].to_numpy(float), blank_mask.to_numpy())
        clean = df["signal"].astype(float)
        if blank_val is not None:
            clean -= blank_val

        df["signal"] = clean
        ctx.blank_used = blank_val
        ctx.data = df
        return ctx


class NormalizeSignal(Step):
    name = "normalize_signal"
    fingerprint_keys = ("data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        df: pd.DataFrame = ctx.data
        cfg = ctx.analysis_config

        norm_fn = get("norm_rule", cfg.norm_rule)

        clean, span = norm_fn(df["signal"])
        df["signal"] = clean

        ctx.norm_span = span
        ctx.data = df
        return ctx


class MaskOutliers(Step):
    name = "mask_outliers"
    fingerprint_keys = ("data",)

    def logic(self, ctx: LBAContext) -> LBAContext:
        df: pd.DataFrame = ctx.data
        cfg = ctx.analysis_config
        out_fn = get("outlier_rule", cfg.outliers.rule)

        mask = pd.Series(False, index=df.index)

        for group_key, group_df in self._iter_groups(df):
            vals = group_df["signal"].to_numpy(float)
            idxs = group_df.index
            if len(vals) < 2:
                continue

            mask.loc[idxs] = out_fn(vals, cfg.outliers)

        df["is_outlier"] = mask
        ctx.data = df
        return ctx

    def _iter_groups(self, df: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
        """
        Yields (name, group_df) for each relevant replicate group.
        """
        if "sample_type" not in df.columns:
            raise ValueError("Missing 'sample_type' column")

        std_mask = df["sample_type"] == "calibration_standard"
        qc_mask = df["sample_type"] == "quality_control"
        sample_mask = df["sample_type"] == "sample"

        if std_mask.any():
            for _, g in df[std_mask].groupby("level_idx"):
                yield "cal_std", g

        if qc_mask.any():
            for _, g in df[qc_mask].groupby("qc_level"):
                yield "qc", g

        if sample_mask.any() and "sample_id" in df.columns:
            for _, g in df[sample_mask].groupby("sample_id"):
                yield "sample", g


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
