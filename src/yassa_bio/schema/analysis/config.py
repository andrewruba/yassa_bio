from __future__ import annotations


from yassa_bio.core.model import SchemaModel
from yassa_bio.schema.analysis.fit import CurveFit
from yassa_bio.schema.analysis.preprocess import Preprocess


class LBAAnalysisConfig(SchemaModel):
    """
    Analysis configuration for ligand-binding assays.
    """

    preprocess: Preprocess = Preprocess()
    curve_fit: CurveFit = CurveFit()
