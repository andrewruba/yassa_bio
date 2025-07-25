import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile

from yassa_bio.evaluation.acceptance.engine.analytical.qc import (
    eval_qc,
)
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.analytical.qc import AnalyticalQCSpec
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


class TestEvalQC:
    def test_all_levels_present_and_pass(self):
        ctx = make_ctx(
            concs=[10, 20, 30, 10, 20, 30],
            signals=[10, 20, 30, 10, 20, 30],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH] * 2,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is True
        assert out["num_pass"] == 6
        assert out["total_wells"] == 6
        for lvl in ("low", "mid", "high"):
            assert out["per_level"][lvl]["meets_level_fraction"]

    def test_missing_pattern_fails(self):
        ctx = make_ctx(
            concs=[10, 20],
            signals=[10, 20],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert "missing_patterns" in out
        assert out["error"].startswith("Missing")

    def test_bias_threshold_violation(self):
        ctx = make_ctx(
            concs=[10, 20, 30],
            signals=[20, 40, 60],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(acc_tol_pct=50)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 0
        for v in out["per_level"].values():
            assert not v["meets_level_fraction"]

    def test_partial_level_failure(self):
        ctx = make_ctx(
            concs=[10, 20, 30, 10, 20, 30],
            signals=[10, 20, 30, 100, 20, 30],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH] * 2,
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(pass_fraction_each_level=0.75)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 5
        assert out["per_level"]["low"]["num_pass"] == 1
        assert out["per_level"]["low"]["meets_level_fraction"] is False

    def test_fraction_total_fails(self):
        ctx = make_ctx(
            concs=[10, 20, 30],
            signals=[10, 200, 300],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID, QCLevel.HIGH],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec(pass_fraction_total=0.8)

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["num_pass"] == 1
        assert out["pass_fraction"] < 0.8

    def test_handles_no_qc_rows(self):
        ctx = make_ctx(
            concs=[],
            signals=[],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["error"] is not None

    def test_qc_level_with_zero_count(self):
        ctx = make_ctx(
            concs=[10, 20],
            signals=[10, 20],
            sample_type=SampleType.QUALITY_CONTROL,
            level_idx=None,
            qc_levels=[QCLevel.LOW, QCLevel.MID],
            back_calc_fn=lambda y: y,
        )
        spec = AnalyticalQCSpec()

        out = eval_qc(ctx, spec)
        assert out["pass"] is False
        assert out["error"] is not None
