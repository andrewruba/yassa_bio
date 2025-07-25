from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
)

from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage
from yassa_bio.core.typing import Percent
from yassa_bio.schema.acceptance.pattern import RequiredWellPattern


class ValidationRecoverySpec(BaseModel):
    """
    Acceptance criteria for extraction recovery (efficiency and consistency).
    """

    required_well_patterns: list[RequiredWellPattern] = Field(
        [
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.MID,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                recovery_stage=RecoveryStage.BEFORE,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.LOW,
                recovery_stage=RecoveryStage.AFTER,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.MID,
                recovery_stage=RecoveryStage.AFTER,
            ),
            RequiredWellPattern(
                sample_type=SampleType.QUALITY_CONTROL,
                qc_level=QCLevel.HIGH,
                recovery_stage=RecoveryStage.AFTER,
            ),
        ],
        description="Minimal list of well patterns that must be present.",
    )

    min_replicates_each: int = Field(
        3,
        ge=1,
        description="Replicate wells for each (stage × QC level) combination.",
    )

    max_cv_pct_within_level: PositiveFloat = Percent(
        15,
        description="CV (%) of recovery at each QC level.",
    )
    max_diff_pct_between_levels: PositiveFloat = Percent(
        15,
        description=("Absolute % difference between mean recoveries at each QC level."),
    )
