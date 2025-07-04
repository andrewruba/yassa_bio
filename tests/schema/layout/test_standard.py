import pytest
from pydantic import ValidationError
from yassa_bio.schema.layout.standard import StandardSeries


class TestStandardSeries:
    def test_all_fields_and_round_trip(self):
        s = StandardSeries(
            start_concentration=1000,
            dilution_factor=3.16,
            num_levels=8,
            concentration_units="ng/mL",
        )
        assert s.start_concentration == 1000
        assert s.dilution_factor == 3.16
        assert s.num_levels == 8
        assert s.concentration_units == "ng/mL"

    def test_num_levels_must_be_two_or_more(self):
        with pytest.raises(ValidationError):
            StandardSeries(
                start_concentration=100,
                dilution_factor=2,
                num_levels=1,
                concentration_units="ng/mL",
            )

    @pytest.mark.parametrize(
        "missing_field, kwargs",
        [
            (
                "start_concentration",
                dict(dilution_factor=2, num_levels=4, concentration_units="ng/mL"),
            ),
            (
                "dilution_factor",
                dict(
                    start_concentration=200, num_levels=4, concentration_units="ng/mL"
                ),
            ),
            (
                "num_levels",
                dict(
                    start_concentration=200,
                    dilution_factor=2,
                    concentration_units="ng/mL",
                ),
            ),
            (
                "concentration_units",
                dict(start_concentration=200, num_levels=4, dilution_factor=2),
            ),
        ],
    )
    def test_missing_required_fields_raise(self, missing_field, kwargs):
        with pytest.raises(ValidationError):
            StandardSeries(**kwargs)

    def test_dilution_factor_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            StandardSeries(
                start_concentration=100,
                dilution_factor="two",
                num_levels=4,
                concentration_units="ng/mL",
            )
