import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from yassa_bio.evaluation.acceptance.engine.validation.accuracy import eval_accuracy
from yassa_bio.schema.acceptance.validation.accuracy import ValidationAccuracySpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import PlateFormat, SampleType, QCLevel
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern


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


class TestEvalAccuracy:
    def test_passes_all_levels(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 15,
                "qc_level": [
                    lvl.qc_level
                    for lvl in ValidationAccuracySpec().required_well_patterns
                    for _ in range(3)
                ],
                "x": [10] * 15,
                "y": [10] * 15,
            }
        )
        spec = ValidationAccuracySpec()
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is True
        assert result["num_pass"] == 5
        assert all(v["pass"] for v in result["per_level"].values())

    def test_fails_missing_qc_level_column(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 3,
                "x": [10, 10, 10],
                "y": [10, 10, 10],
            }
        )
        spec = ValidationAccuracySpec()
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is False
        assert "qc_level" in result["error"]

    def test_fails_missing_required_patterns(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 3,
                "qc_level": [QCLevel.MID] * 3,
                "x": [10] * 3,
                "y": [10] * 3,
            }
        )
        spec = ValidationAccuracySpec()
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is False
        assert "missing_patterns" in result

    def test_fails_due_to_few_replicates(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 2,
                "qc_level": [QCLevel.MID] * 2,
                "x": [10, 10],
                "y": [12, 11],
            }
        )
        spec = ValidationAccuracySpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
                )
            ],
            min_levels=1,
            min_replicates_per_level=3,
        )
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is False
        assert result["per_level"][QCLevel.MID]["n"] == 2
        assert result["per_level"][QCLevel.MID]["pass"] is False

    def test_fails_due_to_total_error(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 3,
                "qc_level": [QCLevel.MID] * 3,
                "x": [10, 10, 10],
                "y": [20, 20, 20],
            }
        )
        spec = ValidationAccuracySpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
                )
            ],
            min_levels=1,
            min_replicates_per_level=3,
            acc_tol_pct_mid=30,
            total_error_pct_mid=50,
        )
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is False
        assert result["per_level"][QCLevel.MID]["total_error_pct"] > 50
        assert result["per_level"][QCLevel.MID]["total_ok"] is False

    def test_mixed_levels_edge_vs_mid(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 6,
                "qc_level": [QCLevel.LLOQ] * 3 + [QCLevel.MID] * 3,
                "x": [10] * 6,
                "y": [9, 10, 11, 12, 10, 8],
            }
        )
        spec = ValidationAccuracySpec(
            required_well_patterns=[
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LLOQ
                ),
                RequiredWellPattern(
                    sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
                ),
            ],
            min_levels=2,
            min_replicates_per_level=3,
            acc_tol_pct_mid=15,
            acc_tol_pct_edge=25,
            total_error_pct_mid=60,
            total_error_pct_edge=80,
        )
        ctx = make_ctx(df)

        result = eval_accuracy(ctx, spec)
        assert result["pass"] is True
        assert result["num_pass"] == 2
        assert result["per_level"][QCLevel.LLOQ]["pass"] is True
        assert result["per_level"][QCLevel.MID]["pass"] is True
