import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from yassa_bio.evaluation.acceptance.engine.validation.carryover import eval_carryover
from yassa_bio.schema.acceptance.validation.carryover import ValidationCarryoverSpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import PlateFormat, SampleType, QCLevel
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria


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
                    sample_type=SampleType.QUALITY_CONTROL,
                    level_idx=None,
                    qc_level=QCLevel.MID,
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
    ctx.curve_back = staticmethod(lambda y: y)
    return ctx


class TestEvalCarryover:
    def test_all_blanks_pass(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"] * 3,
                "carryover": [True] * 3,
                "well": ["A1", "A2", "A3"],
                "signal": [1, 2, 4],
            }
        )
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame(
            {"concentration": [1, 10, 100], "signal": [5, 10, 50]}
        )
        spec = ValidationCarryoverSpec(min_blanks_after_uloq=3)

        result = eval_carryover(ctx, spec)

        assert result["pass"] is True
        assert result["n_blanks"] == 3
        assert result["n_pass"] == 3

    def test_fails_due_to_not_enough_blanks(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"] * 2,
                "carryover": [True, True],
                "well": ["A1", "A2"],
                "signal": [5, 5],
            }
        )
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame(
            {"concentration": [1, 10, 100], "signal": [2, 10, 50]}
        )
        spec = ValidationCarryoverSpec(min_blanks_after_uloq=3)

        result = eval_carryover(ctx, spec)
        assert result["pass"] is False
        assert "expected ≥" in result["error"]

    def test_fails_due_to_signal_above_lloq(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"] * 3,
                "carryover": [True] * 3,
                "well": ["A1", "A2", "A3"],
                "signal": [1, 5, 12],
            }
        )
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame(
            {"concentration": [1, 10, 100], "signal": [5, 10, 50]}
        )
        spec = ValidationCarryoverSpec(min_blanks_after_uloq=3)

        result = eval_carryover(ctx, spec)
        assert result["pass"] is False
        assert result["n_pass"] == 1
        assert any(not r["pass"] for r in result["per_blank"])

    def test_fails_due_to_missing_lloq_signal(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"] * 3,
                "carryover": [True] * 3,
                "well": ["A1", "A2", "A3"],
                "signal": [5, 6, 7],
            }
        )
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [], "signal": []})
        spec = ValidationCarryoverSpec(min_blanks_after_uloq=1)

        result = eval_carryover(ctx, spec)
        assert result["pass"] is False
        assert "Invalid LLOQ signal" in result["error"]

    def test_fails_due_to_missing_required_pattern(self):
        df = pd.DataFrame(
            {
                "sample_type": ["blank"] * 3,
                "carryover": [False, False, False],
                "well": ["A1", "A2", "A3"],
                "signal": [5, 5, 5],
            }
        )
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [1], "signal": [10]})
        spec = ValidationCarryoverSpec()

        result = eval_carryover(ctx, spec)
        assert result["pass"] is False
        assert "missing_patterns" in result
