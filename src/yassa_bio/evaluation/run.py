import logging

from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.evaluation.analysis.preprocess import Preprocess
from yassa_bio.evaluation.analysis.fit import CurveFit
from yassa_bio.evaluation.acceptance.router import Acceptance
from yassa_bio.evaluation.acceptance.analytical import Analytical
from yassa_bio.evaluation.acceptance.validation import Validation
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.acceptance.analytical import LBAAnalyticalAcceptanceCriteria


pipe = Pipeline(
    [
        Preprocess(),
        CurveFit(),
        Acceptance(
            criteria={
                LBAValidationAcceptanceCriteria: Validation(),
                LBAAnalyticalAcceptanceCriteria: Analytical(),
            }
        ),
    ]
)


def run(
    batch_data: BatchData | PlateData,
    analysis_config: LBAAnalysisConfig,
    acceptance_criteria: (
        LBAValidationAcceptanceCriteria | LBAAnalyticalAcceptanceCriteria
    ),
) -> LBAContext:
    logging.basicConfig(level=logging.INFO)
    ctx = pipe.run(
        LBAContext(
            batch_data=batch_data,
            analysis_config=analysis_config,
            acceptance_criteria=acceptance_criteria,
        )
    )
    return ctx
