from typing import Callable, Any
import numpy as np
import pandas as pd
from pydantic import Field
from pydantic.config import ConfigDict

from lilpipe.models import PipelineContext
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.layout.plate import PlateData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria


class LBAContext(PipelineContext):
    # Lock down model config
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=False,
        arbitrary_types_allowed=True,
    )

    # Inputs
    batch_data: BatchData | PlateData
    analysis_config: LBAAnalysisConfig
    acceptance_criteria: LBAAnalyticalAcceptanceCriteria

    # Preprocess
    data: pd.DataFrame | None = None
    excluded_data: pd.DataFrame | None = None
    blank_used: float | None = None
    norm_span: float | None = None

    # Curve fit
    calib_df: pd.DataFrame | None = None
    curve_fwd: Callable[[np.ndarray], np.ndarray] | None = None
    curve_back: Callable[[np.ndarray], np.ndarray] | None = None
    curve_params: np.ndarray | None = None
    dropped_cal_wells: pd.DataFrame | None = None

    # Acceptance
    acceptance_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    acceptance_history: list[dict[str, dict[str, Any]]] = Field(default_factory=list)
    acceptance_pass: bool | None = None
