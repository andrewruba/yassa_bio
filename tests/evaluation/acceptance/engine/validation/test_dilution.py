import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from yassa_bio.evaluation.acceptance.engine.validation.dilution import (
    eval_dilution_linearity,
)
from yassa_bio.schema.acceptance.validation.dilution import (
    ValidationDilutionLinearitySpec,
)
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


class TestEvalDilutionLinearity:
    def test_passes_all(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": "quality_control",
                        "qc_level": QCLevel.MID,
                        "level_idx": i,
                        "x": 10,
                        "y": 10,
                    }
                    for i in [1, 1, 1, 2, 2, 2, 3, 3, 3]
                ],
                {
                    "sample_type": "quality_control",
                    "qc_level": QCLevel.ABOVE_ULOQ,
                    "level_idx": 99,
                    "x": 100,
                    "y": 100,
                },
            ]
        )
        spec = ValidationDilutionLinearitySpec()
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame(
            {"concentration": [1, 10, 50], "signal": [1, 10, 50]}
        )

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is True
        assert result["hook_failures"] == 0
        assert len(result["per_point"]) == 3
        assert all(p["pass"] for p in result["per_point"])

    def test_fails_due_to_missing_patterns(self):
        df = pd.DataFrame(
            {
                "sample_type": ["sample"] * 3,
                "level_idx": [1, 2, 3],
                "qc_level": [None] * 3,
                "x": [10, 10, 10],
                "y": [10, 10, 10],
            }
        )
        spec = ValidationDilutionLinearitySpec()
        ctx = make_ctx(df)

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert "missing_patterns" in result

    def test_fails_due_to_few_replicates(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": "quality_control",
                        "qc_level": QCLevel.MID,
                        "level_idx": i,
                        "x": 10,
                        "y": 10,
                    }
                    for i in [1, 1, 2, 2, 2]
                ],
                {
                    "sample_type": "quality_control",
                    "qc_level": QCLevel.ABOVE_ULOQ,
                    "level_idx": 99,
                    "x": 100,
                    "y": 100,
                },
            ]
        )
        spec = ValidationDilutionLinearitySpec(min_replicates=3)
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [50], "signal": [50]})

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert any(p["n"] < spec.min_replicates for p in result["per_point"])

    def test_fails_due_to_accuracy(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": "quality_control",
                        "qc_level": QCLevel.MID,
                        "level_idx": i,
                        "x": 10,
                        "y": 20,
                    }
                    for i in [1, 1, 1, 2, 2, 2, 3, 3, 3]
                ],
                {
                    "sample_type": "quality_control",
                    "qc_level": QCLevel.ABOVE_ULOQ,
                    "level_idx": 99,
                    "x": 100,
                    "y": 100,
                },
            ]
        )
        spec = ValidationDilutionLinearitySpec(acc_tol_pct=10)
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [50], "signal": [50]})

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert any(not p["acc_ok"] for p in result["per_point"])

    def test_fails_due_to_cv(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": "quality_control",
                        "qc_level": QCLevel.MID,
                        "level_idx": i,
                        "x": 10,
                        "y": y,
                    }
                    for i, y in zip([1, 1, 1, 2, 2, 2], [10, 12, 8, 10, 12, 8])
                ],
                {
                    "sample_type": "quality_control",
                    "qc_level": QCLevel.ABOVE_ULOQ,
                    "level_idx": 99,
                    "x": 100,
                    "y": 100,
                },
            ]
        )
        spec = ValidationDilutionLinearitySpec(cv_tol_pct=5)
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [50], "signal": [50]})

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert any(not p["cv_ok"] for p in result["per_point"])

    def test_fails_due_to_too_few_levels(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": "quality_control",
                        "qc_level": QCLevel.MID,
                        "level_idx": 1,
                        "x": 10,
                        "y": 10,
                    }
                    for _ in range(6)
                ],
                {
                    "sample_type": "quality_control",
                    "qc_level": QCLevel.ABOVE_ULOQ,
                    "level_idx": 99,
                    "x": 100,
                    "y": 100,
                },
            ]
        )
        spec = ValidationDilutionLinearitySpec(min_dilutions=3)
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [50], "signal": [50]})

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert result["num_dilution_levels"] < spec.min_dilutions

    def test_hook_fails_due_to_recovery_and_not_above_uloq(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 4,
                "qc_level": [QCLevel.ABOVE_ULOQ] * 2 + [QCLevel.MID] * 2,
                "level_idx": [1, 2, 3, 3],
                "x": [100, 100, 10, 10],
                "y": [80, 60, 10, 10],
                "well": ["W1", "W2", "W3", "W4"],
            }
        )
        spec = ValidationDilutionLinearitySpec(undiluted_recovery_min_pct=90)
        ctx = make_ctx(df)
        ctx.calib_df = pd.DataFrame({"concentration": [100], "signal": [100]})
        ctx.curve_back = staticmethod(lambda y: y)

        result = eval_dilution_linearity(ctx, spec)
        assert result["pass"] is False
        assert result["hook_failures"] > 0
        assert any(not h["hook_ok"] for h in result["hook_checks"])
