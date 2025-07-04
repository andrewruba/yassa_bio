from __future__ import annotations


from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.fit import CurveFit
from yassa_bio.schema.analysis.preprocessing import Preprocessing


class LBAAnalysisConfig(SchemaModel):
    """
    Analysis configuration for ligand-binding assays.
    """

    preprocessing: Preprocessing = Preprocessing()
    curve_fit: CurveFit = CurveFit()
