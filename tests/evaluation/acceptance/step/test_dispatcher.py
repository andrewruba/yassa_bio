import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile

from yassa_bio.evaluation.acceptance.step.dispatcher import EvaluateSpecs
from yassa_bio.schema.analysis.enum import Transformation, CurveModel, Weighting
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria
from yassa_bio.schema.acceptance.analytical.qc import AnalyticalQCSpec
from yassa_bio.schema.acceptance.analytical.calibration import AnalyticalCalibrationSpec
from yassa_bio.schema.acceptance.analytical.parallelism import ParallelismSpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate
import yassa_bio.core.registry as _reg


class MockCalSpec(AnalyticalCalibrationSpec):
    pass


class MockQCSpec(AnalyticalQCSpec):
    pass


class MockParallelismSpec(ParallelismSpec):
    pass


def make_mock_ctx() -> LBAContext:
    df = pd.DataFrame(
        {
            "signal": [2.0, 4.0],
            "concentration": [1.0, 2.0],
            "sample_type": ["calibration_standard", "calibration_standard"],
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

    batch = BatchData(plates=[plate])

    return LBAContext(
        batch_data=batch,
        analysis_config=LBAAnalysisConfig(
            preprocess={},
            curve_fit={
                "transformation_x": Transformation.IDENTITY,
                "transformation_y": Transformation.IDENTITY,
                "weighting": Weighting.ONE,
                "model": CurveModel.LINEAR,
            },
        ),
        acceptance_criteria=LBAAnalyticalAcceptanceCriteria(
            calibration=MockCalSpec(),
            qc=MockQCSpec(),
            parallelism=MockParallelismSpec(),
        ),
    )


class TestEvaluateSpecs:
    @pytest.fixture(autouse=True)
    def isolate_registry(self):
        snapshot = _reg._registry.copy()
        _reg._registry.clear()
        try:
            yield
        finally:
            _reg._registry.clear()
            _reg._registry.update(snapshot)

    @staticmethod
    def _register_mock():
        @_reg.register("acceptance", MockCalSpec.__name__)
        def fake_cal_fn(ctx: LBAContext, spec: object) -> dict:
            return {"pass": True, "mock_result": "cal_pass"}

        @_reg.register("acceptance", MockQCSpec.__name__)
        def fake_qc_fn(ctx: LBAContext, spec: object) -> dict:
            return {"pass": True, "mock_result": "qc_pass"}

        @_reg.register("acceptance", MockParallelismSpec.__name__)
        def fake_par_fn(ctx: LBAContext, spec: object) -> dict:
            return {"pass": True, "mock_result": "par_pass"}

    def test_dispatch_and_stores_results(self):
        self._register_mock()
        ctx = make_mock_ctx()
        ctx = EvaluateSpecs().run(ctx)
        ctx = EvaluateSpecs().run(ctx)

        assert "calibration" in ctx.acceptance_results
        assert "qc" in ctx.acceptance_results
        assert "parallelism" in ctx.acceptance_results
        assert ctx.acceptance_results["calibration"]["mock_result"] == "cal_pass"
        assert ctx.acceptance_results["qc"]["mock_result"] == "qc_pass"
        assert ctx.acceptance_results["parallelism"]["mock_result"] == "par_pass"
        assert ctx.acceptance_pass is True
        assert len(ctx.acceptance_history) == 2
        assert ctx.acceptance_history[-1] == ctx.acceptance_results
