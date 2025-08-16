import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile


from yassa_bio.evaluation.acceptance.step.validation import Validation
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate


def make_ctx() -> LBAContext:
    df = pd.DataFrame(
        {
            "sample_type": ["quality_control"],
            "x": [1],
            "y": [1],
            "qc_level": ["mid"],
        }
    )

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
        acceptance_criteria=LBAValidationAcceptanceCriteria(),
        acceptance_results={},
    )
    ctx.data = df.copy()
    ctx.curve_back = staticmethod(lambda y: y)
    return ctx


class TestValidation:
    def test_runs_evaluate_specs_only(self, mocker):
        ctx = make_ctx()

        mocker.patch(
            "yassa_bio.evaluation.acceptance.step.validation.EvaluateSpecs.logic",
            return_value=ctx,
        )

        result = Validation().run(ctx)

        assert isinstance(result, LBAContext)
        assert "evaluate_specs" in result.step_meta
        assert result.step_meta["evaluate_specs"]["status"] == "ok"
