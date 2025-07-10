from __future__ import annotations

import pytest
from pydantic import ValidationError

from yassa_bio.schema.analysis.preprocess import (
    OutlierParams,
    Preprocess,
)
from yassa_bio.schema.analysis.enum import (
    OutlierRule,
    BlankRule,
    NormRule,
)


class TestOutlierParams:
    def test_default_ok(self):
        p = OutlierParams()
        assert p.rule is OutlierRule.NONE
        assert p.z_threshold == 3.0

    def test_full_custom_param_set(self):
        p = OutlierParams(
            rule=OutlierRule.IQR,
            z_threshold=5.0,
            grubbs_alpha=0.02,
            iqr_k=2.2,
        )

        dumped = p.model_dump(mode="json")
        assert dumped["rule"] == "iqr"
        assert dumped["iqr_k"] == 2.2
        assert p.iqr_k == 2.2
        assert p.rule is OutlierRule.IQR

    @pytest.mark.parametrize("bad_zscore", [-0.1, 0])
    def test_zscore_requires_threshold(self, bad_zscore):
        with pytest.raises(ValidationError):
            OutlierParams(rule=OutlierRule.ZSCORE, z_threshold=bad_zscore)

    @pytest.mark.parametrize("bad_alpha", [-0.1, 0, 1.2])
    def test_grubbs_alpha_range(self, bad_alpha):
        with pytest.raises(ValidationError):
            OutlierParams(rule=OutlierRule.GRUBBS, grubbs_alpha=bad_alpha)

    @pytest.mark.parametrize("bad_k", [0, -1, -2.5])
    def test_iqr_positive_k(self, bad_k):
        with pytest.raises(ValidationError):
            OutlierParams(rule=OutlierRule.IQR, iqr_k=bad_k)


class TestPreprocess:
    def test_defaults_round_trip(self):
        pp = Preprocess()
        assert pp.blank_rule is BlankRule.MEAN
        assert pp.norm_rule is NormRule.NONE
        assert pp.outliers.rule is OutlierRule.NONE

    def test_all_flags_non_default(self):
        custom_outliers = OutlierParams(
            rule=OutlierRule.GRUBBS,
            grubbs_alpha=0.01,
        )
        pp = Preprocess(
            blank_rule=BlankRule.NONE,
            norm_rule=NormRule.SPAN,
            outliers=custom_outliers,
        )

        assert pp.blank_rule is BlankRule.NONE
        assert pp.norm_rule is NormRule.SPAN

        assert pp.outliers.rule is OutlierRule.GRUBBS
        assert pp.outliers.grubbs_alpha == 0.01

        dumped = pp.model_dump(mode="json")
        assert dumped["blank_rule"] == "none"
        assert dumped["norm_rule"] == "span"
        assert dumped["outliers"]["rule"] == "grubbs"
        assert dumped["outliers"]["grubbs_alpha"] == 0.01

    def test_custom_outlier_block(self):
        custom = OutlierParams(rule=OutlierRule.ZSCORE, z_threshold=4.0)
        pp = Preprocess(outliers=custom, norm_rule=NormRule.SPAN)
        assert pp.outliers.z_threshold == 4.0
        assert pp.norm_rule is NormRule.SPAN

    def test_invalid_nested_outlier_bubbles_up(self):
        bad = {"rule": "zscore", "z_threshold": None}
        with pytest.raises(ValidationError):
            Preprocess(outliers=bad)
