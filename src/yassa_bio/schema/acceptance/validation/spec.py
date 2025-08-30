from pydantic import BaseModel

from yassa_bio.schema.acceptance.validation.specificity import ValidationSpecificitySpec
from yassa_bio.schema.acceptance.validation.selectivity import ValidationSelectivitySpec
from yassa_bio.schema.acceptance.validation.calibration import ValidationCalibrationSpec
from yassa_bio.schema.acceptance.validation.accuracy import ValidationAccuracySpec
from yassa_bio.schema.acceptance.validation.precision import ValidationPrecisionSpec
from yassa_bio.schema.acceptance.validation.carryover import ValidationCarryoverSpec
from yassa_bio.schema.acceptance.validation.dilution import (
    ValidationDilutionLinearitySpec,
)
from yassa_bio.schema.acceptance.validation.stability import ValidationStabilitySpec


class LBAValidationAcceptanceCriteria(BaseModel):
    """
    Acceptance criteria for ligand binding assay (LBA) validation runs.
    """

    specificity: ValidationSpecificitySpec = ValidationSpecificitySpec()
    selectivity: ValidationSelectivitySpec = ValidationSelectivitySpec()
    calibration: ValidationCalibrationSpec = ValidationCalibrationSpec()
    accuracy: ValidationAccuracySpec = ValidationAccuracySpec()
    precision: ValidationPrecisionSpec = ValidationPrecisionSpec()
    carryover: ValidationCarryoverSpec = ValidationCarryoverSpec()
    dilution_linearity: ValidationDilutionLinearitySpec = (
        ValidationDilutionLinearitySpec()
    )
    stability: ValidationStabilitySpec = ValidationStabilitySpec()
