from __future__ import annotations
import pandas as pd
import logging

from lilpipe.step import Step
from yassa_bio.evaluation.acceptance.step.dispatcher import EvaluateSpecs
from yassa_bio.evaluation.context import LBAContext

log = logging.getLogger(__name__)


class CheckRerun(Step):
    """
    Drop failing calibration levels (when refit is allowed) and trigger a pipeline
    rerun, which skips the remaining Analytical steps.
    """

    name = "check_rerun"

    def __init__(self) -> None:
        super().__init__(name=self.name)

    def logic(self, ctx: LBAContext) -> LBAContext:
        cal_res = ctx.acceptance_results.get("calibration", {})
        if cal_res.get("pass", False):
            return ctx

        if cal_res.get("can_refit", False):
            failing_levels = set(cal_res.get("failing_levels", []))
            if not failing_levels:
                return ctx

            log.info(
                "🔄  Will refit: discarding %d failing calibration level(s): %s",
                len(failing_levels),
                sorted(failing_levels),
            )

            df: pd.DataFrame = ctx.data
            mask_fail = df["sample_type"].eq("calibration_standard") & df[
                "concentration"
            ].isin(failing_levels)
            ctx.dropped_cal_wells = df.loc[mask_fail].copy()

            ctx.data = df.loc[~mask_fail].reset_index(drop=True)
            ctx.calib_df = None

            ctx.abort_pass()

        return ctx


class Analytical(Step):
    name = "analytical"

    def __init__(self) -> None:
        super().__init__(
            name=self.name,
            children=[
                EvaluateSpecs(),
                CheckRerun(),
            ],
        )
