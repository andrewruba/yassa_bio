import pytest
import pandas as pd

from yassa_bio.schema.acceptance.pattern import RequiredWellPattern
from yassa_bio.schema.layout.enum import SampleType, QCLevel


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
                "stability_condition_time": [None, None, "after"],
                "matrix_type": [None, None, "lipemic"],
                "matrix_source_id": [None, None, "donor_3"],
            }
        )

    def test_mask_with_qc_level(self, base_df):
        pat = RequiredWellPattern(
            sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
        )
        mask = pat.mask(base_df)
        assert mask.sum() == 1
        assert mask.iloc[0]

    def test_present_true(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.BLANK, carryover=True)
        assert pat.present(base_df)

    def test_present_false(self, base_df):
        pat = RequiredWellPattern(sample_type=SampleType.SAMPLE, carryover=True)
        assert not pat.present(base_df)
