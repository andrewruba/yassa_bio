import numpy as np
import pandas as pd
import pytest
import tempfile

from yassa_bio.evaluation.analysis.step.preprocess import (
    LoadData,
    CheckData,
    ExcludeData,
    SubtractBlank,
    NormalizeSignal,
    MaskOutliers,
    Preprocess,
)
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData, PlateLayout
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.layout.enum import SampleType, PlateFormat
from yassa_bio.schema.layout.file import PlateReaderFile
from datetime import datetime
from pathlib import Path
from yassa_bio.schema.analysis.enum import BlankRule, NormRule, OutlierRule
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria


def make_plate(
    df: pd.DataFrame,
    sample_type: SampleType = SampleType.SAMPLE,
    extra_wells: list[WellTemplate] = [],
) -> PlateData:
    """Returns a PlateData with a minimal layout and .df preloaded (in temp file)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = Path(tmp.name)

    wells = extra_wells or [
        WellTemplate(well="A1", file_row=0, file_col=0, sample_type=sample_type)
    ]

    plate = PlateData(
        source_file=PlateReaderFile(
            path=tmp_path,
            run_date=datetime(2025, 1, 1, 12),
            instrument="pytest",
            operator="pytest",
        ),
        plate_id="P1",
        layout=PlateLayout(plate_format=PlateFormat.FMT_96, wells=wells),
    )
    plate._df = df.copy()
    plate._mtime = tmp_path.stat().st_mtime
    return plate


def make_ctx(
    df: pd.DataFrame,
    *,
    blank_rule: BlankRule = BlankRule.MEAN,
    norm_rule: NormRule = NormRule.SPAN,
    outlier_rule: OutlierRule = OutlierRule.ZSCORE,
    z_threshold: float = 1.0,
) -> LBAContext:
    """Creates LBAContext with configurable preprocessing rules and df."""
    preprocess_cfg = {
        "blank_rule": blank_rule,
        "norm_rule": norm_rule,
        "outliers": {
            "rule": outlier_rule,
            "z_threshold": z_threshold,
        },
    }

    cfg = LBAAnalysisConfig(preprocess=preprocess_cfg)
    plate = make_plate(df)
    batch = BatchData(plates=[plate])

    return LBAContext(
        batch_data=batch,
        analysis_config=cfg,
        acceptance_criteria=LBAValidationAcceptanceCriteria(),
    )


class Dummy:
    pass


class TestLoadData:
    def test_load_data_success(self):
        df = pd.DataFrame({"signal": [1], "concentration": [1]})
        ctx = make_ctx(df)
        ctx = LoadData().run(ctx)

        assert ctx.data.equals(df)

    def test_load_data_missing_df_attr(self):
        df = pd.DataFrame({"signal": [1], "concentration": [1]})
        ctx = make_ctx(df)
        # hot-swap batch_data with invalid object
        ctx.batch_data = Dummy()

        with pytest.raises(TypeError, match=r"\.df property"):
            LoadData().run(ctx)


class TestCheckData:
    def test_check_data_ok(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 2.0],
                "concentration": [1, 2],
                "sample_type": "sample",
                "exclude": False,
            }
        )
        ctx = LoadData().run(make_ctx(df))
        CheckData().run(ctx)

    @pytest.mark.parametrize(
        "bad_df, exp_exc, exp_msg",
        [
            (pd.DataFrame({"signal": [1, 2]}), ValueError, "Missing required columns"),
            (
                pd.DataFrame(
                    columns=["signal", "concentration", "sample_type", "exclude"]
                ),
                ValueError,
                "DataFrame is empty",
            ),
            (
                pd.DataFrame(
                    {
                        "signal": ["a", "b"],
                        "concentration": [1, 2],
                        "sample_type": "sample",
                        "exclude": False,
                    }
                ),
                TypeError,
                "'signal' column must be numeric",
            ),
        ],
    )
    def test_check_data_failures(self, bad_df, exp_exc, exp_msg):
        ctx = LoadData().run(make_ctx(bad_df))
        with pytest.raises(exp_exc, match=exp_msg):
            CheckData().run(ctx)

    def test_check_data_non_dataframe(self):
        ctx = make_ctx(df=pd.DataFrame())
        ctx.data = ["not", "a", "frame"]

        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            CheckData().run(ctx)


class TestExcludeData:
    def test_excludes_rows_marked_true(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 2.0, 3.0],
                "concentration": [0, 1, 2],
                "sample_type": "sample",
                "exclude": [False, True, False],
            }
        )

        ctx = LoadData().run(make_ctx(df))
        out = ExcludeData().run(ctx)

        assert len(out.data) == 2
        assert len(out.excluded_data) == 1
        assert out.excluded_data.iloc[0]["signal"] == 2.0
        assert "exclude" in out.data.columns

    def test_exclude_fills_na_as_false(self):
        df = pd.DataFrame(
            {
                "signal": [5.0, 6.0],
                "concentration": [1, 2],
                "sample_type": "sample",
                "exclude": [None, False],
            }
        )

        ctx = LoadData().run(make_ctx(df))
        out = ExcludeData().run(ctx)

        assert len(out.data) == 2
        assert len(out.excluded_data) == 0


class TestSubtractBlank:
    def test_subtracts_mean_blank(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 2.0, 10.0],
                "concentration": [1, 2, 3],
                "sample_type": [SampleType.BLANK, SampleType.BLANK, "sample"],
                "exclude": False,
            }
        )
        ctx = LoadData().run(make_ctx(df))
        out = SubtractBlank().run(ctx)

        assert np.isclose(out.blank_used, 1.5)
        assert np.isclose(out.data.loc[2, "signal"], 8.5)
        assert out.data.loc[:1, "signal"].tolist() == [-0.5, 0.5]
        assert pd.api.types.is_float_dtype(out.data["signal"])

    def test_no_blanks_leaves_signal(self):
        df = pd.DataFrame(
            {
                "signal": [5.0, 6.0],
                "concentration": [1, 2],
                "sample_type": "sample",
                "exclude": False,
            }
        )
        ctx = LoadData().run(make_ctx(df))
        out = SubtractBlank().run(ctx)

        assert out.blank_used is None
        assert out.data["signal"].tolist() == [5.0, 6.0]

    def test_subtracts_median_blank_rule(self):
        df = pd.DataFrame(
            {
                "signal": [2.0, 8.0, 10.0],
                "concentration": [0, 0, 0],
                "sample_type": [SampleType.BLANK, SampleType.BLANK, "sample"],
                "exclude": False,
            }
        )
        ctx = LoadData().run(make_ctx(df, blank_rule=BlankRule.MEDIAN))
        out = SubtractBlank().run(ctx)

        assert np.isclose(out.blank_used, 5.0)
        assert np.isclose(out.data.loc[2, "signal"], 5.0)


class TestNormalizeSignal:
    def test_span_normalises_and_sets_span(self):
        df = pd.DataFrame(
            {
                "signal": [0.0, 10.0, 5.0],
                "concentration": [0, 10, 5],
                "sample_type": [
                    SampleType.CALIBRATION_STANDARD,
                    SampleType.CALIBRATION_STANDARD,
                    "sample",
                ],
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, norm_rule=NormRule.SPAN))
        out = NormalizeSignal().run(ctx)

        assert out.data["signal"].tolist() == [0.0, 1.0, 0.5]
        assert out.norm_span == 10

    def test_span_no_calibration_keeps_signal(self):
        df = pd.DataFrame(
            {
                "signal": [3.0, 7.0],
                "concentration": np.nan,
                "sample_type": "sample",
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, norm_rule=NormRule.SPAN))
        out = NormalizeSignal().run(ctx)

        assert out.data["signal"].tolist() == [3.0, 7.0]
        assert out.norm_span is None

    def test_span_zero_span_keeps_signal(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 2.0],
                "concentration": [5, 5],
                "sample_type": [
                    SampleType.CALIBRATION_STANDARD,
                    SampleType.CALIBRATION_STANDARD,
                ],
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, norm_rule=NormRule.SPAN))
        out = NormalizeSignal().run(ctx)

        assert out.data["signal"].tolist() == [1.0, 2.0]
        assert out.norm_span is None

    def test_max_rule_divides_by_max(self):
        df = pd.DataFrame(
            {
                "signal": [2.0, 4.0, 10.0],
                "concentration": [5, 10, 10],
                "sample_type": [
                    SampleType.CALIBRATION_STANDARD,
                    SampleType.CALIBRATION_STANDARD,
                    "sample",
                ],
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, norm_rule=NormRule.MAX))
        out = NormalizeSignal().run(ctx)

        assert out.data["signal"].tolist() == [0.2, 0.4, 1.0]
        assert out.norm_span == 10

    def test_max_rule_no_calibration_keeps_signal(self):
        df = pd.DataFrame(
            {
                "signal": [6.0, 9.0],
                "concentration": np.nan,
                "sample_type": "sample",
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, norm_rule=NormRule.MAX))
        out = NormalizeSignal().run(ctx)

        assert out.data["signal"].tolist() == [6.0, 9.0]
        assert out.norm_span is None


class TestMaskOutliers:
    def test_zscore_flags_outlier_within_each_group(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 1.1, 10.0, 2.0, 2.1],
                "concentration": np.nan,
                "sample_type": "quality_control",
                "qc_level": "mid",
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, z_threshold=1.0))
        out = MaskOutliers().run(ctx)

        assert np.sum(out.data["is_outlier"]) == 1
        assert out.data.loc[2, "is_outlier"]
        assert out.data.loc[[3, 4], "is_outlier"].eq(False).all()

    def test_group_with_single_point_is_never_flagged(self):
        df = pd.DataFrame(
            {
                "signal": [5.0],
                "concentration": [1],
                "sample_type": ["calibration_standard"],
                "level_idx": [1],
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df))
        out = MaskOutliers().run(ctx)
        assert out.data["is_outlier"].sum() == 0

    def test_calibration_grouping(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 100.0, 1.1, 1.2, 1.3, 1.4],
                "concentration": [1, 1, 2, 1, 1, 2],
                "sample_type": "calibration_standard",
                "level_idx": [1, 1, 2, 1, 1, 2],
                "exclude": False,
            }
        )
        ctx = LoadData().run(make_ctx(df, z_threshold=1.0))
        out = MaskOutliers().run(ctx)

        assert out.data.loc[1, "is_outlier"]
        assert not out.data.loc[2, "is_outlier"]

    def test_qc_grouping_flags_within_each_level(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 100.0, 1.1, 1.2, 1.3, 1.4],
                "concentration": np.nan,
                "sample_type": "quality_control",
                "qc_level": ["low", "low", "high", "high", "low", "low"],
                "exclude": False,
            }
        )

        ctx = LoadData().run(make_ctx(df, z_threshold=1.0))
        out = MaskOutliers().run(ctx)

        assert out.data.loc[1, "is_outlier"]
        assert out.data["is_outlier"].sum() == 1


class TestPreprocessComposite:
    def test_full_pipeline_flags_outlier_and_sets_meta(self):
        df = pd.DataFrame(
            {
                "signal": [1.0, 1.1, 100.0, 1.2, 1.3, 1.4],
                "concentration": np.nan,
                "sample_type": "quality_control",
                "qc_level": "mid",
                "exclude": False,
            }
        )

        ctx_in = make_ctx(df)
        ctx_out = Preprocess().run(ctx_in)

        assert ctx_out.blank_used is None
        assert ctx_out.norm_span is None

        assert "is_outlier" in ctx_out.data.columns
        assert ctx_out.data["is_outlier"].sum() == 1
        assert ctx_out.data.loc[2, "is_outlier"]

        expected_children = {
            s.name
            for s in (
                LoadData(),
                CheckData(),
                ExcludeData(),
                SubtractBlank(),
                NormalizeSignal(),
                MaskOutliers(),
            )
        }
        assert expected_children.issubset(ctx_out.step_meta.keys())

        for name in expected_children:
            m = ctx_out.step_meta[name]
            assert m["status"] == "ok"
            assert "duration" in m and m["duration"] >= 0
