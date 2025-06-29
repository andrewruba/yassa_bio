import pytest
from pydantic import BaseModel, ValidationError, NonNegativeFloat

from yassa_bio.core.typing import Percent, Fraction01


class TestPercentAndFraction01:

    class Demo(BaseModel):
        pct: NonNegativeFloat = Percent(50)
        prob: NonNegativeFloat = Fraction01()

    class TempLimits(BaseModel):
        celsius: float = Percent(22, lo=-20, hi=80)

    @pytest.mark.parametrize("good_pct", [0, 1, 42.5, 99.9, 100])
    @pytest.mark.parametrize("good_prob", [0, 0.0001, 0.3, 0.9999, 1])
    def test_demo_accepts_valid_numbers(self, good_pct, good_prob):
        d = self.Demo(pct=good_pct, prob=good_prob)
        assert d.pct == good_pct
        assert d.prob == good_prob

    @pytest.mark.parametrize("bad_pct", [-0.1, -1, 100.1, 101, 1_000])
    def test_percent_out_of_range_raises(self, bad_pct):
        with pytest.raises(ValidationError):
            self.Demo(pct=bad_pct, prob=0.5)

    @pytest.mark.parametrize("bad_prob", [-0.1, 1.01, 2])
    def test_fraction_out_of_range_raises(self, bad_prob):
        with pytest.raises(ValidationError):
            self.Demo(pct=10, prob=bad_prob)

    def test_custom_percent_window_accepts_and_rejects(self):
        assert self.TempLimits(celsius=-10).celsius == -10

        with pytest.raises(ValidationError):
            self.TempLimits(celsius=90)
