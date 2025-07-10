from pydantic import BaseModel

from yassa_bio.schema.acceptance.validation.specificity import SpecificitySpec
from yassa_bio.schema.acceptance.validation.selectivity import SelectivitySpec
from yassa_bio.schema.acceptance.validation.calibration import CalibrationSpec
from yassa_bio.schema.acceptance.validation.accuracy import AccuracySpec
from yassa_bio.schema.acceptance.validation.precision import PrecisionSpec
from yassa_bio.schema.acceptance.validation.carryover import CarryoverSpec
from yassa_bio.schema.acceptance.validation.dilution import DilutionLinearitySpec
from yassa_bio.schema.acceptance.validation.stability import StabilitySpec
from yassa_bio.schema.acceptance.validation.parallelism import ParallelismSpec
from yassa_bio.schema.acceptance.validation.recovery import RecoverySpec


class LBAValidationAcceptanceCriteria(BaseModel):
    specificity: SpecificitySpec = SpecificitySpec()
    selectivity: SelectivitySpec = SelectivitySpec()
    calibration: CalibrationSpec = CalibrationSpec()
    accuracy: AccuracySpec = AccuracySpec()
    precision: PrecisionSpec = PrecisionSpec()
    carryover: CarryoverSpec = CarryoverSpec()
    dilution_linearity: DilutionLinearitySpec = DilutionLinearitySpec()
    stability: StabilitySpec = StabilitySpec()
    parallelism: ParallelismSpec = ParallelismSpec()
    recovery: RecoverySpec = RecoverySpec()
