from pydantic import BaseModel
from typing import Optional

from yassa_bio.schema.layout.enum import SampleType, QCLevel, RecoveryStage
from yassa_bio.schema.layout.well import WellTemplate


class RequiredWellPattern(BaseModel):
    sample_type: SampleType
    qc_level: Optional[QCLevel] = None
    needs_interferent: bool = False
    carryover: bool = False
    needs_stability_condition: bool = False
    needs_sample_id: bool = False
    recovery_stage: Optional[RecoveryStage] = None

    def matches(self, well: WellTemplate) -> bool:
        if well.sample_type != self.sample_type:
            return False

        if self.qc_level is not None and well.qc_level != self.qc_level:
            return False

        if self.needs_interferent != (well.interferent is not None):
            return False

        if well.carryover != self.carryover:
            return False

        if self.needs_stability_condition != (well.stability_condition is not None):
            return False

        if self.recovery_stage is not None and (
            well.recovery_stage != self.recovery_stage
        ):
            return False

        return True
