from typing import Dict
from yassa_bio.schema.layout.standard import StandardSeries


def series_concentration_map(series: StandardSeries) -> Dict[int, float]:
    """
    Return a mapping {level_idx -> nominal concentration} for a serially
    diluted `StandardSeries`.

    Level indices are 1-based: 1 is the top standard (C₀),
    2 is C₀ / dilution_factor, …, N is the last prepared level.

    Example
    -------
    >>> ser = StandardSeries(start_concentration=100, dilution_factor=2, num_levels=4)
    >>> series_concentration_map(ser)
    {1: 100.0, 2: 50.0, 3: 25.0, 4: 12.5}
    """
    return {
        lvl: series.start_concentration / (series.dilution_factor ** (lvl - 1))
        for lvl in range(1, series.num_levels + 1)
    }
