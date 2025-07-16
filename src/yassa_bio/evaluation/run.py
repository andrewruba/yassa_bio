import logging

from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.evaluation.analysis.step.preprocess import Preprocess
from yassa_bio.evaluation.analysis.step.fit import CurveFit
from yassa_bio.evaluation.acceptance.step.router import Acceptance
from yassa_bio.evaluation.acceptance.step.analytical import Analytical
from yassa_bio.evaluation.acceptance.step.validation import Validation
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


# TODO:
# 1) if we rerun an analytical run with a failed calibration curve,
# it will reload the full df in LoadData when it needs to use the
# filtered df from CheckRerun
