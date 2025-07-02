from __future__ import annotations

from pydantic import model_validator

from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.calibration import CalibrationCurve, CarryoverCheck
from yassa_bio.schema.analysis.fit import CurveFit, PotencyOptions
from yassa_bio.schema.analysis.qc import QCSpec
from yassa_bio.schema.analysis.sample import SampleProcessing


class LigandBindingAnalysisConfig(SchemaModel):
    """
    Top-level configuration for ligand-binding analysis.
    """

    curve_fit: CurveFit = CurveFit()
    potency: PotencyOptions = PotencyOptions()
    qc: QCSpec = QCSpec()
    sample: SampleProcessing = SampleProcessing()
    calibration: CalibrationCurve = CalibrationCurve()
    carryover: CarryoverCheck = CarryoverCheck()

    @model_validator(mode="after")
    def _inject_curve_model_for_potency(self):
        self.potency.set_curve_model(self.curve_fit.model)
        return self


# TODO:
# - sensible defaults (or required inputs) for all fields
#   for data mapping and analysis config.
# - add example values for all fields (data mapping and analysis config schema)
#   that make sense, account for potential None values.
# - review regulatory docs
# - can there be weighting for both x and y?
# - Possible transformations may include log, square root, or reciprocal,
#   although other transformations are acceptable. Address this.
