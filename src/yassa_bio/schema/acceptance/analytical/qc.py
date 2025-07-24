from pydantic import BaseModel, Field, PositiveFloat
from typing import List

from yassa_bio.core.typing import Percent, Fraction01
from yassa_bio.schema.layout.enum import SampleType, QCLevel
from yassa_bio.schema.acceptance.validation.pattern import RequiredWellPattern


class QCSpec(BaseModel):
    """
    Acceptance criteria for accuracy/precision on QC samples in an analytical run.
    """

    required_well_patterns: List[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.LOW
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.MID
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL, qc_level=QCLevel.HIGH
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    acc_tol_pct: PositiveFloat = Percent(
        20, description="Per-well accuracy tolerance (± %)."
    )
    pass_fraction_total: PositiveFloat = Fraction01(
        2 / 3,
        description="Fraction of QC wells that must pass accuracy.",
    )
    pass_fraction_each_level: PositiveFloat = Fraction01(
        0.50,
        description="Fraction of wells at every QC level that must pass.",
    )
