from __future__ import annotations

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.calibration import CalibrationCurve, CarryoverCheck
from yassa_bio.schema.analysis.fit import CurveFit, PotencyOptions
from yassa_bio.schema.analysis.qc import QCSpec
from yassa_bio.schema.analysis.sample import SampleProcessing


class LigandBindingAnalysisConfig(SchemaModel):
    curve_fit: CurveFit = CurveFit()
    potency: PotencyOptions = PotencyOptions()
    qc: QCSpec = QCSpec()
    sample: SampleProcessing = SampleProcessing()
    calibration: CalibrationCurve = CalibrationCurve()
    carryover: CarryoverCheck = CarryoverCheck()


# TODO:
# - analytical_range is a data object not a config object, should be moved to a more appropriate place
# - normalize_to_control is a free-form string, should be more structured
# - review regulatory requirements for ligand binding assays and ensure all necessary parameters are included and grouped in the way that makes sense according to those requirements.
