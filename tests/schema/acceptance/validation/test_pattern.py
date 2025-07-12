import pytest
import pandas as pd

from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage


class TestRequiredWellPattern:
    @pytest.fixture
    def base_df(self):
        return pd.DataFrame(
            {
                "sample_type": ["quality_control", "blank", "quality_control"],
                "qc_level": ["low", "mid", None],
                "interferent": [None, "glucose", None],
                "carryover": [False, True, False],
                "stability_condition": [None, None, "long-term"],
                "recovery_stage": ["before", None, "after"],
                "sample_id": ["id1", None, "id2"],
            }
        )

    def test_mask_with_qc_level(self, base_df):
        pat = RequiredWellPattern(
            sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
        )
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[0]

    def test_mask_with_interferent(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.BLANK, needs_interferent=True)
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[1]

    def test_mask_with_carryover(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.BLANK, carryover=True)
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[1]

    def test_mask_with_stability_condition(self, base_df):
        pat = RequiredWellPattern(
            sample_type=SampleType.QUALITY_CONTROL, needs_stability_condition=True
        )
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[2]

    def test_mask_with_recovery_stage(self, base_df):
        pat = RequiredWellPattern(
            sample_type=SampleType.QUALITY_CONTROL, recovery_stage=RecoveryStage.BEFORE
        )
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[0]

    def test_mask_with_sample_id(self, base_df):
        pat = RequiredWellPattern(
            sample_type=SampleType.QUALITY_CONTROL, needs_sample_id=True
        )
        mask = pat.mask(base_df)
        assert mask.sum() == 2
        assert mask.iloc[[0, 2]].all()

    def test_present_true(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.BLANK, carryover=True)
        assert pat.present(base_df)

    def test_present_false(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.SAMPLE, carryover=True)
        assert not pat.present(base_df)
