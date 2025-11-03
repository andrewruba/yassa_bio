import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from yassa_bio.evaluation.analysis.step.fit import (
    SelectCalibrationData,
    ApplyTransforms,
    ComputeWeights,
    FitCalibrationData,
    CurveFit,
)
from yassa_bio.evaluation.analysis.step.preprocess import LoadData
from yassa_bio.schema.analysis.enum import Transformation, Weighting, CurveModel
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate


def make_ctx(
    df: pd.DataFrame,
    *,
    transformation_x: Transformation = Transformation.LOG10,
    transformation_y: Transformation = Transformation.IDENTITY,
    weighting: Weighting = Weighting.ONE,
    model: CurveModel = CurveModel.LINEAR,
) -> LBAContext:
    cfg = LBAAnalysisConfig(
        preprocess={},
        curve_fit={
            "transformation_x": transformation_x,
            "transformation_y": transformation_y,
            "weighting": weighting,
            "model": model,
        },
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
        analysis_config=cfg,
        acceptance_criteria=LBAAnalyticalAcceptanceCriteria(),
    )


class TestSelectCalibrationData:
    def test_selects_only_calibration_rows(self):
        df = pd.DataFrame(
            {
                "signal": [1, 2, 3],
                "concentration": [0.1, 0.2, 0.3],
                "sample_type": [
                    "calibration_standard",
                    "sample",
                    "calibration_standard",
                ],
            }
        )
        ctx = LoadData().run(make_ctx(df))
        ctx = SelectCalibrationData().run(ctx)

        assert ctx.calib_df.shape[0] == 2
        assert (ctx.calib_df["sample_type"] == "calibration_standard").all()

    def test_raises_if_no_calibration(self):
        df = pd.DataFrame(
            {
                "signal": [1, 2],
                "concentration": [0.1, 0.2],
                "sample_type": ["sample", "sample"],
            }
        )
        ctx = LoadData().run(make_ctx(df))

        with pytest.raises(ValueError, match="No calibration-standard wells"):
            SelectCalibrationData().run(ctx)


class TestApplyTransforms:
    def test_applies_log_transform_x_and_identity_y(self):
        df = pd.DataFrame(
            {
                "signal": [1, 10],
                "concentration": [1, 10],
                "sample_type": ["calibration_standard", "calibration_standard"],
            }
        )
        ctx = LoadData().run(make_ctx(df))
        ctx = ApplyTransforms().run(ctx)
        ctx = SelectCalibrationData().run(ctx)

        assert np.allclose(ctx.calib_df["x"], [0.0, 1.0])
        assert np.allclose(ctx.calib_df["y"], [1, 10])


class TestComputeWeights:
    def test_identity_weights_sets_ones(self):
        df = pd.DataFrame(
            {
                "signal": [1, 2],
                "concentration": [1, 2],
                "sample_type": ["calibration_standard", "calibration_standard"],
            }
        )
        ctx = LoadData().run(make_ctx(df))
        ctx = ApplyTransforms().run(ctx)
        ctx = ComputeWeights().run(ctx)
        ctx = SelectCalibrationData().run(ctx)

        assert np.allclose(ctx.calib_df["w"], [1.0, 1.0])


class TestFitCalibrationData:
    def test_fits_linear_model(self):
        df = pd.DataFrame(
            {
                "signal": [2.0, 4.0],
                "concentration": [1.0, 2.0],
                "sample_type": ["calibration_standard", "calibration_standard"],
            }
        )
        ctx = LoadData().run(make_ctx(df))
        ctx = ApplyTransforms().run(ctx)
        ctx = ComputeWeights().run(ctx)
        ctx = SelectCalibrationData().run(ctx)
        ctx = FitCalibrationData().run(ctx)

        assert callable(ctx.curve_fwd)
        assert callable(ctx.curve_back)
        assert isinstance(ctx.curve_params, np.ndarray)

        assert np.isclose(
            ctx.curve_fwd(ctx.calib_df["x"][0]),
            2.0,
            atol=1e-6,  # transformed
        )
        assert np.isclose(
            ctx.curve_back([4.0]),
            ctx.calib_df["x"][1],
            atol=1e-6,  # transformed
        )


class TestCurveFit:
    def test_full_composite_runs_and_sets_fields(self):
        df = pd.DataFrame(
            {
                "signal": [2.0, 4.0],
                "concentration": [1.0, 2.0],
                "sample_type": ["calibration_standard", "calibration_standard"],
            }
        )
        ctx = LoadData().run(make_ctx(df))
        ctx = CurveFit().run(ctx)

        assert callable(ctx.curve_fwd)
        assert callable(ctx.curve_back)
        assert isinstance(ctx.curve_params, np.ndarray)

        expected_steps = {
            SelectCalibrationData.name,
            ApplyTransforms.name,
            ComputeWeights.name,
            FitCalibrationData.name,
        }
        assert expected_steps.issubset(ctx.step_meta)
        for name in expected_steps:
            m = ctx.step_meta[name]
            assert m["status"] == "ok"
            assert "duration" in m
