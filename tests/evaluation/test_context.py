import pytest
from pydantic import ValidationError

from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.layout.plate import PlateData
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.file import PlateReaderFile
from yassa_bio.schema.layout.plate import PlateLayout
from yassa_bio.schema.layout.enum import PlateFormat, SampleType
from yassa_bio.schema.layout.well import WellTemplate
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria


@pytest.fixture
def dummy_plate():
    well = WellTemplate(
        well="A1", file_row=0, file_col=0, sample_type=SampleType.SAMPLE
    )
    layout = PlateLayout(wells=[well], plate_format=PlateFormat.FMT_96)
    file = PlateReaderFile(path="dummy.csv")
    return PlateData(source_file=file, plate_id="P1", layout=layout)


@pytest.fixture
def dummy_batch(dummy_plate):
    return BatchData(plates=[dummy_plate])


@pytest.fixture
def dummy_analysis():
    return LBAAnalysisConfig()


class TestLBAContext:
    def test_valid_lba_context_with_validation(self, dummy_batch, dummy_analysis):
        criteria = LBAValidationAcceptanceCriteria()
        ctx = LBAContext(
            batch_data=dummy_batch,
            analysis_config=dummy_analysis,
            acceptance_criteria=criteria,
        )
        assert ctx.batch_data == dummy_batch
        assert ctx.analysis_config == dummy_analysis
        assert ctx.acceptance_criteria == criteria

    def test_valid_lba_context_with_analytical(self, dummy_batch, dummy_analysis):
        criteria = LBAAnalyticalAcceptanceCriteria()
        ctx = LBAContext(
            batch_data=dummy_batch,
            analysis_config=dummy_analysis,
            acceptance_criteria=criteria,
        )
        assert ctx.acceptance_criteria == criteria

    def test_invalid_lba_context_raises(self):
        with pytest.raises(ValidationError):
            LBAContext(
                batch_data="not a batch or plate",
                analysis_config=LBAAnalysisConfig(),
                acceptance_criteria=LBAValidationAcceptanceCriteria(),
            )
