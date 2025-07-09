from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.evaluation.analysis.preprocess import Preprocess

pipe = Pipeline(
    [
        Preprocess(),
    ]
)

# from yassa_bio.pipeline.base import PipelineContext
# import logging
# logging.basicConfig(level=logging.INFO)
# ctx = pipe.run(PipelineContext(data=batch.df, config=analysis_config))
