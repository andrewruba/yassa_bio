import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile

from yassa_bio.evaluation.acceptance.engine.analytical.calibration import (
    eval_calibration,
)
from yassa_bio.schema.acceptance.analytical.calibration import AnalyticalCalibrationSpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import (
    LBAAnalyticalAcceptanceCriteria,
)


def make_ctx(
    *,
    concs,
    signals,
    sample_type: SampleType,
    level_idx=1,
    qc_levels=None,
    back_calc_fn,
) -> LBAContext:
    df = pd.DataFrame(
        {
            "concentration": concs,
            "signal": signals,
            "x": concs,
            "y": signals,
            "sample_type": sample_type.value,
            "qc_level": None,
        }
    )

    if qc_levels:
        df["qc_level"] = [lvl.value for lvl in qc_levels]

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
                    sample_type=sample_type,
                    level_idx=level_idx,
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
    ctx.curve_back = staticmethod(back_calc_fn)

    return ctx


class TestEvalCalibration:
    def test_all_levels_pass(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[1, 2, 3, 4, 5, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is True
        assert out["num_pass"] == out["num_levels"]
        assert out["can_refit"] is True
        assert out["failing_levels"] == []

    def test_one_edge_fails_but_can_refit(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6, 7],
            signals=[1.1, 2, 3, 4, 5, 6, 100],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert 7 in out["failing_levels"]
        assert out["can_refit"] is True

    def test_too_many_levels_fail(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[100, 100, 3, 4, 5, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert set(out["failing_levels"]) >= {1, 2}
        assert out["can_refit"] is False

    def test_not_enough_retained_levels(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[100, 2, 3, 4, 100, 6],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec(min_retained_levels=5)

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert out["can_refit"] is False

    def test_too_few_levels_total(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5],
            signals=[1, 2, 3, 4, 5],
            sample_type=SampleType.CALIBRATION_STANDARD,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec(min_levels=6)

        out = eval_calibration(ctx, spec)
        assert out["num_levels"] == 5
        assert out["pass"] is False

    def test_fails_missing_required_patterns(self):
        ctx = make_ctx(
            concs=[1, 2, 3, 4, 5, 6],
            signals=[1, 2, 3, 4, 5, 6],
            sample_type=SampleType.SAMPLE,
            level_idx=None,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalCalibrationSpec()

        out = eval_calibration(ctx, spec)
        assert out["pass"] is False
        assert "missing_patterns" in out
        assert "calibration pattern" in out["error"]
