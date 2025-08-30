from pydantic import BaseModel

from yassa_bio.schema.acceptance.analytical.calibration import AnalyticalCalibrationSpec
from yassa_bio.schema.acceptance.analytical.qc import AnalyticalQCSpec


class LBAAnalyticalAcceptanceCriteria(BaseModel):
    """
    Acceptance criteria for routine ligand binding assay (LBA) study-sample runs.
    """

    calibration: AnalyticalCalibrationSpec = AnalyticalCalibrationSpec()
    qc: AnalyticalQCSpec = AnalyticalQCSpec()
