from __future__ import annotations

from yassa_bio.core.model import StrictModel
from yassa_bio.schema.analysis.calibration import CalibrationCurve, CarryoverCheck
from yassa_bio.schema.analysis.fit import CurveFit, PotencyOptions
from yassa_bio.schema.analysis.qc import QCSpec
from yassa_bio.schema.analysis.sample import SampleProcessing


class LigandBindingAnalysisConfig(StrictModel):
    curve_fit: CurveFit = CurveFit()
    potency: PotencyOptions = PotencyOptions()
    qc: QCSpec = QCSpec()
    sample: SampleProcessing = SampleProcessing()
    calibration: CalibrationCurve = CalibrationCurve()
    carryover: CarryoverCheck = CarryoverCheck()


# TODO:
# - add validator for potency.method to ensure it matches curve_fit.model
# - ensure each group has min number of replicates for analysis especially after outlier removal
# - address '±25 % for LLOQ/ULOQ handled in code' comment in CalibrationCurve, should be in config
# - carry-over should should address "Carry-over in the blank samples following the highest calibration standard should not be greater than 20% of the analyte response at the LLOQ and 5% of the response for the IS."
# - we have intra-dilution CV criteria, but not inter-dilution CV criteria, should we add that?
# - qc_id in ControlWindow is freetext, should we use a more structured approach to match? Currently, we have just "control". Could we add control_high, control_low, control_blank, etc.?
# - add limits to certain fields, e.g. min_levels_pass in LinearityRules.
# - add description fields to all models for clarity
# - review regulatory requirements for ligand binding assays and ensure all necessary parameters are included and grouped in the way that makes sense according to those requirements.
