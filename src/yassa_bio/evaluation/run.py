import logging

from lilpipe.engine import Pipeline
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.evaluation.analysis.step.preprocess import Preprocess
from yassa_bio.evaluation.analysis.step.fit import CurveFit
from yassa_bio.evaluation.acceptance.step.router import Acceptance
from yassa_bio.evaluation.acceptance.step.analytical import Analytical
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria


pipe = Pipeline(
    name="LBA Analysis Pipeline",
    steps=[
        Preprocess(),
        CurveFit(),
        Acceptance(
            criteria={
                LBAAnalyticalAcceptanceCriteria: Analytical(),
            }
        ),
    ],
    max_passes=3,
)


def run(
    batch_data: BatchData | PlateData,
    analysis_config: LBAAnalysisConfig,
    acceptance_criteria: LBAAnalyticalAcceptanceCriteria,
) -> LBAContext:
    """
    Run the full LBA analysis and acceptance pipeline.

    Parameters
    ----------
    batch_data : BatchData or PlateData
        The input data to analyze. Typically a `BatchData` containing one or more
        plates, or a single `PlateData` if analyzing one plate in isolation.

    analysis_config : LBAAnalysisConfig
        Configuration specifying preprocessing, curve fitting, and modeling rules.

    acceptance_criteria :
        LBAAnalyticalAcceptanceCriteria
        Which type of acceptance criteria to use:
        - Use `LBAAnalyticalAcceptanceCriteria` for routine analytical runs

    Returns
    -------
    LBAContext
        The analysis context after the pipeline has been run. This object contains
        all intermediate and final results (e.g. fitted curve, evaluation metrics),
        and can be further inspected or serialized.

    Notes
    -----
    - This is the main entry point for using the pipeline programmatically.
    - Logging is enabled at INFO level by default.
    - The pipeline will automatically dispatch to the appropriate acceptance steps
      depending on the type of criteria passed in.
    - Some steps and features are under active development, and the API may change.

    Example
    -------
    ```python
    ctx = run(batch_data=batch, analysis_config=config, acceptance_criteria=criteria)
    print(ctx.acceptance_results)
    ```
    """
    logging.basicConfig(level=logging.INFO)
    ctx = pipe.run(
        LBAContext(
            batch_data=batch_data,
            analysis_config=analysis_config,
            acceptance_criteria=acceptance_criteria,
        )
    )
    return ctx
