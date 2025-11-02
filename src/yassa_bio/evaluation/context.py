from yassa_bio.pipeline.base import PipelineContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria


class LBAContext(PipelineContext):
    batch_data: BatchData | PlateData
    analysis_config: LBAAnalysisConfig
    acceptance_criteria: LBAAnalyticalAcceptanceCriteria
