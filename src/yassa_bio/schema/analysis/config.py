from __future__ import annotations
from pydantic import model_validator

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

    @model_validator(mode="after")
    def _cross_checks(self):
        # provide curve_model to potency validator
        self.potency.__pydantic_extra__ = {"_curve_model": self.curve_fit.model}

        if (
            self.qc.standards_nominal is not None
            and len(self.qc.standards_nominal) < self.calibration.min_levels
        ):
            raise ValueError("qc.standards_nominal shorter than calibration.min_levels")
        return self


# TODO:
# - standards_nominal is unclear in terms of its purpose and how it relates to the calibration curve
# - analytical_range is unclear in terms of its purpose and how it relates to the calibration curve
# - normalize_to_control is a free-form string, should be more structured
# - review regulatory requirements for ligand binding assays and ensure all necessary parameters are included and grouped in the way that makes sense according to those requirements.
