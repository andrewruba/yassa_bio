from pydantic import BaseModel

from yassa_bio.schema.acceptance.analytical.calibration import CalibrationSpec
from yassa_bio.schema.acceptance.analytical.qc import QCSpec
from yassa_bio.schema.acceptance.analytical.parallelism import ParallelismSpec


class LBAAnalyticalAcceptanceCriteria(BaseModel):
    """
    Acceptance criteria for routine ligand binding assay study-sample runs.
    """

    calibration: CalibrationSpec = CalibrationSpec()
    qc: QCSpec = QCSpec()
    parallelism: ParallelismSpec = ParallelismSpec()
