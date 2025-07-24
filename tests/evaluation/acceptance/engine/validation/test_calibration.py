import pandas as pd

from yassa_bio.evaluation.acceptance.engine.validation.calibration import (
    eval_calibration_validation,
)
from yassa_bio.schema.acceptance.validation.calibration import CalibrationSpec
from yassa_bio.schema.layout.enum import SampleType
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import PlateFormat
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from datetime import datetime
from pathlib import Path
import tempfile


def make_ctx(df: pd.DataFrame) -> LBAContext:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = Path(tmp.name)

    plate = PlateData(
        source_file=PlateReaderFile(
            path=tmp_path,
            run_date=datetime.now(),
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
        acceptance_criteria=LBAValidationAcceptanceCriteria(),
        acceptance_results={},
    )
    ctx.data = df.copy()
    ctx.calib_df = df.copy()
    ctx.curve_back = staticmethod(lambda y: y)
    return ctx


class TestEvalCalibrationValidation:
    def test_passes_all_levels(self):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3, 4, 5, 6],
                "signal": [1, 2, 3, 4, 5, 6],
                "x": [1, 2, 3, 4, 5, 6],
                "y": [1, 2, 3, 4, 5, 6],
                "sample_type": ["calibration_standard"] * 6,
            }
        )
        spec = CalibrationSpec()
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is True
        assert out["num_levels"] == 6
        assert out["num_pass"] == 6

    def test_fails_due_to_bad_accuracy(self):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3],
                "signal": [100, 2, 3],
                "x": [1, 2, 3],
                "y": [100, 2, 3],
                "sample_type": ["calibration_standard"] * 3,
            }
        )
        spec = CalibrationSpec(min_levels=3, pass_fraction=0.8)
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is False
        assert out["num_levels"] == 3
        assert out["num_pass"] < 3

    def test_fails_due_to_cv_exceeding(self):
        df = pd.DataFrame(
            {
                "concentration": [1] * 3 + [5] * 3,
                "signal": [1, 2, 3, 5, 5, 5],
                "x": [1, 1, 1, 5, 5, 5],
                "y": [1, 2, 3, 5, 5, 5],
                "sample_type": ["calibration_standard"] * 6,
            }
        )
        spec = CalibrationSpec(
            min_levels=2, pass_fraction=1.0, cv_tol_pct_edge=10, cv_tol_pct_mid=10
        )
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is False
        assert out["per_level"][1]["cv_ok"] is False

    def test_edge_and_mid_thresholds_applied(self):
        df = pd.DataFrame(
            {
                "concentration": [1, 2, 3],
                "signal": [1, 2, 3],
                "x": [1, 2, 3],
                "y": [1.2, 2, 3],  # slight bias on LLOQ
                "sample_type": ["calibration_standard"] * 3,
            }
        )
        spec = CalibrationSpec(acc_tol_pct_edge=25, acc_tol_pct_mid=5, min_levels=3)
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is True
        assert out["per_level"][1]["is_edge"]
        assert out["per_level"][2]["acc_ok"] is True

    def test_missing_required_pattern(self):
        df = pd.DataFrame(
            {
                "concentration": [1],
                "signal": [1],
                "x": [1],
                "y": [1],
                "sample_type": ["quality_control"],
            }
        )
        spec = CalibrationSpec()
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is False
        assert "missing_patterns" in out

    def test_empty_input(self):
        df = pd.DataFrame(columns=["concentration", "signal", "x", "y", "sample_type"])
        spec = CalibrationSpec()
        ctx = make_ctx(df)

        out = eval_calibration_validation(ctx, spec)
        assert out["pass"] is False
        assert out["error"] == "calib_df is empty"
