from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.evaluation.analysis.preprocess import Preprocess
from yassa_bio.evaluation.analysis.fit import CurveFit
from yassa_bio.evaluation.acceptance.router import Acceptance
from yassa_bio.evaluation.acceptance.analytical import Analytical
from yassa_bio.evaluation.acceptance.validation import Validation


pipe = Pipeline(
    [
        Preprocess(),
        CurveFit(),
        Acceptance(
            criteria={
                "validation": Validation(),
                "analytical": Analytical(),
            }
        ),
    ]
)

# def run():
#     logging.basicConfig(level=logging.INFO)
#     ctx = pipe.run(PipelineContext(data=batch.df, config=analysis_config))
