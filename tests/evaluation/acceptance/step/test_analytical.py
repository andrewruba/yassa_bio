import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
from lilpipe.enums import PipelineSignal

from yassa_bio.evaluation.acceptance.step.analytical import CheckRerun, Analytical
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import (
    LBAAnalyticalAcceptanceCriteria,
)
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate


def make_ctx(df: pd.DataFrame, cal_res: dict = {}) -> LBAContext:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = Path(tmp.name)

    plate = PlateData(
        source_file=PlateReaderFile(
            path=tmp_path,
            run_date=datetime(2025, 1, 1, 12),
            instrument="pytest",
            operator="pytest",
        ),
        plate_id="P1",
        layout=PlateLayout(
            plate_format=PlateFormat.FMT_96,
            wells=[
                WellTemplate(
                    well="A1",
                    file_row=0,
                    file_col=0,
                    sample_type=SampleType.CALIBRATION_STANDARD,
                    level_idx=1,
                )
            ],
        ),
    )
    plate._df = df.copy()
    plate._mtime = tmp_path.stat().st_mtime

    ctx = LBAContext(
        batch_data=BatchData(plates=[plate]),
        analysis_config=LBAAnalysisConfig(preprocess={}, curve_fit={}),
        acceptance_criteria=LBAAnalyticalAcceptanceCriteria(),
        acceptance_results={},
    )
    ctx.data = df.copy()
    ctx.calib_df = df.copy()
    ctx.curve_back = staticmethod(lambda y: y)
    ctx.acceptance_results["calibration"] = cal_res
    return ctx


class TestCheckRerun:
    def test_skips_if_passed(self):
        df = pd.DataFrame(
            {
                "concentration": [1, 2],
                "sample_type": ["calibration_standard", "calibration_standard"],
            }
        )
        ctx = make_ctx(df, {"pass": True})
        out = CheckRerun().run(ctx)

        assert out.data.equals(df)
        assert out.signal == PipelineSignal.CONTINUE

    def test_skips_if_no_failing_levels(self):
        df = pd.DataFrame(
            {"concentration": [1], "sample_type": ["calibration_standard"]}
        )
        ctx = make_ctx(df, {"pass": False, "can_refit": True, "failing_levels": []})
        out = CheckRerun().run(ctx)

        assert out.data.equals(df)
        assert out.signal == PipelineSignal.CONTINUE

    def test_discards_failing_levels_and_flags_rerun(self):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3],
                "sample_type": [
                    "calibration_standard",
                    "sample",
                    "calibration_standard",
                ],
            }
        )
        ctx = make_ctx(df, {"pass": False, "can_refit": True, "failing_levels": [1]})
        out = CheckRerun().run(ctx)

        assert out.signal == PipelineSignal.ABORT_PASS
        assert out.calib_df is None
        assert isinstance(out.dropped_cal_wells, pd.DataFrame)
        assert out.dropped_cal_wells["concentration"].tolist() == [1]
        assert out.data["concentration"].tolist() == [2, 3]
        assert out.data.reset_index(drop=True).equals(out.data)

    def test_handles_no_matching_rows(self):
        df = pd.DataFrame(
            {"concentration": [5, 6], "sample_type": ["sample", "sample"]}
        )
        ctx = make_ctx(df, {"pass": False, "can_refit": True, "failing_levels": [1]})
        out = CheckRerun().run(ctx)

        assert out.signal == PipelineSignal.ABORT_PASS
        assert out.calib_df is None
        assert out.dropped_cal_wells.empty
        assert out.data.equals(df)


class TestAnalytical:
    def test_runs_all_steps_if_no_rerun_needed(self, mocker):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3],
                "signal": [1, 2, 3],
                "x": [1, 2, 3],
                "y": [1, 2, 3],
                "sample_type": "calibration_standard",
                "qc_level": None,
            }
        )
        ctx = make_ctx(df)

        mocker.patch(
            "yassa_bio.evaluation.acceptance.step.analytical.EvaluateSpecs.logic",
            return_value=ctx,
        )

        out = Analytical().run(ctx)
        assert out.signal == PipelineSignal.CONTINUE
        assert "evaluate_specs" in out.step_meta
        assert "check_rerun" in out.step_meta
        assert out.step_meta["check_rerun"]["status"] == "ok"

    def test_aborts_after_checkrerun_if_needs_rerun(self, mocker):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3, 4],
                "signal": [1, 2, 3, 4],
                "x": [1, 2, 3, 4],
                "y": [1, 2, 3, 100],
                "sample_type": "calibration_standard",
                "qc_level": None,
            }
        )
        ctx = make_ctx(df)

        ctx.acceptance_results["calibration"] = {
            "pass": False,
            "can_refit": True,
            "failing_levels": [4],
        }

        mocker.patch(
            "yassa_bio.evaluation.acceptance.step.analytical.EvaluateSpecs.logic",
            return_value=ctx,
        )

        out = Analytical().run(ctx)

        assert out.signal == PipelineSignal.ABORT_PASS
        assert "check_rerun" in out.step_meta
        assert out.dropped_cal_wells["concentration"].tolist() == [4]
        assert out.data["concentration"].tolist() == [1, 2, 3]
