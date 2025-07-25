import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from yassa_bio.evaluation.acceptance.engine.validation.stability import eval_stability
from yassa_bio.schema.acceptance.validation.stability import ValidationStabilitySpec
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import (
    PlateFormat,
    SampleType,
    QCLevel,
    StabilityConditionTime,
)
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


class TestEvalStability:
    def test_passes_all_conditions(self):
        df = pd.DataFrame(
            [
                *[
                    {
                        "sample_type": SampleType.QUALITY_CONTROL.value,
                        "qc_level": level,
                        "stability_condition": cond,
                        "stability_condition_time": time,
                        "y": y,
                    }
                    for level, cond, y in [
                        (QCLevel.LOW, "freeze-thaw", 10),
                        (QCLevel.HIGH, "long-term", 20),
                    ]
                    for time in [StabilityConditionTime.BEFORE] * 3
                    + [StabilityConditionTime.AFTER] * 3
                ]
            ]
        )
        spec = ValidationStabilitySpec(min_conditions=2)
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is True
        assert result["num_conditions"] == 2
        assert result["pass_fraction"] == 1.0

    def test_fails_no_stability_annotations(self):
        df = pd.DataFrame(
            {
                "sample_type": ["quality_control"] * 6,
                "qc_level": [QCLevel.LOW, QCLevel.HIGH] * 3,
                "stability_condition": [None] * 6,
                "stability_condition_time": [None] * 6,
                "y": [10] * 6,
            }
        )
        spec = ValidationStabilitySpec()
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert "error" in result
        assert "Missing" in result["error"]

    def test_fails_missing_required_patterns(self):
        df = pd.DataFrame.from_records(
            [
                {
                    "sample_type": SampleType.QUALITY_CONTROL.value,
                    "qc_level": QCLevel.LOW,
                    "stability_condition": "autosampler",
                    "stability_condition_time": StabilityConditionTime.BEFORE,
                    "y": 10,
                }
            ]
        )
        spec = ValidationStabilitySpec()
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is False
        assert "missing_patterns" in result

    def test_fails_missing_before_or_after(self):
        df = pd.DataFrame.from_records(
            [
                {
                    "sample_type": SampleType.QUALITY_CONTROL.value,
                    "qc_level": qc_level,
                    "stability_condition": "freeze-thaw",
                    "stability_condition_time": StabilityConditionTime.BEFORE,
                    "y": 10,
                }
                for qc_level in [QCLevel.LOW, QCLevel.HIGH]
            ]
        )
        spec = ValidationStabilitySpec()
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is False
        assert all(
            "BEFORE or AFTER" in r.get("error", "")
            for r in result["per_condition"].values()
        )

    def test_fails_due_to_zero_mean_before(self):
        df = pd.concat(
            [
                pd.DataFrame.from_records(
                    [
                        {
                            "sample_type": SampleType.QUALITY_CONTROL.value,
                            "qc_level": level,
                            "stability_condition": "freeze-thaw",
                            "stability_condition_time": StabilityConditionTime.BEFORE,
                            "y": 0,
                        }
                        for _ in range(3)
                    ]
                )
                for level in [QCLevel.LOW, QCLevel.HIGH]
            ]
            + [
                pd.DataFrame.from_records(
                    [
                        {
                            "sample_type": SampleType.QUALITY_CONTROL.value,
                            "qc_level": level,
                            "stability_condition": "freeze-thaw",
                            "stability_condition_time": StabilityConditionTime.AFTER,
                            "y": y,
                        }
                        for y in [10, 10, 10, 0, 0, 0, 10, 10, 10]
                    ]
                )
                for level in [QCLevel.LOW, QCLevel.HIGH]
            ],
            ignore_index=True,
        )
        spec = ValidationStabilitySpec()
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is False
        assert "Zero mean" in next(iter(result["per_condition"].values()))["error"]

    def test_fails_due_to_bias_exceeding_tolerance(self):
        df = pd.DataFrame.from_records(
            [
                {
                    "sample_type": SampleType.QUALITY_CONTROL.value,
                    "qc_level": qc_level,
                    "stability_condition": "lt",
                    "stability_condition_time": time,
                    "y": 10 if time == StabilityConditionTime.BEFORE else 15,
                }
                for qc_level in [QCLevel.HIGH, QCLevel.LOW]
                for time in [StabilityConditionTime.BEFORE] * 3
                + [StabilityConditionTime.AFTER] * 3
            ]
        )
        spec = ValidationStabilitySpec(acc_tol_pct=20)
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is False
        assert result["pass_fraction"] < 1.0
        assert not next(iter(result["per_condition"].values()))["pass"]

    def test_fails_due_to_too_few_conditions(self):
        df = pd.DataFrame.from_records(
            [
                {
                    "sample_type": SampleType.QUALITY_CONTROL.value,
                    "qc_level": qc_level,
                    "stability_condition": "only",
                    "stability_condition_time": time,
                    "y": 10,
                }
                for qc_level in [QCLevel.LOW, QCLevel.HIGH]
                for time in [
                    StabilityConditionTime.BEFORE,
                    StabilityConditionTime.AFTER,
                ]
                * 3
            ]
        )
        spec = ValidationStabilitySpec(min_conditions=2)
        ctx = make_ctx(df)

        result = eval_stability(ctx, spec)
        assert result["pass"] is False
        assert result["num_conditions"] < spec.min_conditions
