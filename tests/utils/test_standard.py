# tests/test_standards.py
from yassa_bio.utils.standard import series_concentration_map
from yassa_bio.schema.layout.standard import StandardSeries


class TestSeriesConcentrationMap:
    def test_basic_dilution_series(self):
        ser = StandardSeries(
            start_concentration=100,
            dilution_factor=2,
            num_levels=4,
            concentration_units="ng/mL",
        )
        expected = {1: 100.0, 2: 50.0, 3: 25.0, 4: 12.5}
        assert series_concentration_map(ser) == expected

    def test_single_step_dilution_factor(self):
        ser = StandardSeries(
            start_concentration=60,
            dilution_factor=3,
            num_levels=3,
            concentration_units="ng/mL",
        )
        # 60, 20, 6.666…
        out = series_concentration_map(ser)
        assert out[1] == 60
        assert out[2] == 20
        assert round(out[3], 3) == 6.667

    def test_float_dilution_factor(self):
        ser = StandardSeries(
            start_concentration=1_000,
            dilution_factor=1.5,
            num_levels=3,
            concentration_units="ng/mL",
        )
        # 1000, 666.666…, 444.444…
        out = series_concentration_map(ser)
        assert out[2] == ser.start_concentration / ser.dilution_factor
        assert out[3] == ser.start_concentration / (ser.dilution_factor**2)

    def test_num_levels_respected(self):
        ser = StandardSeries(
            start_concentration=10,
            dilution_factor=2,
            num_levels=2,
            concentration_units="ng/mL",
        )
        result = series_concentration_map(ser)
        assert set(result.keys()) == {1, 2}

    def test_mapping_is_monotonically_decreasing(self):
        ser = StandardSeries(
            start_concentration=256,
            dilution_factor=2,
            num_levels=5,
            concentration_units="ng/mL",
        )
        concs = list(series_concentration_map(ser).values())
        assert concs == sorted(concs, reverse=True)
