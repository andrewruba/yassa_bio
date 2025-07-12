from __future__ import annotations

from yassa_bio.pipeline.composite import CompositeStep
from yassa_bio.evaluation.acceptance.step.dispatcher import EvaluateSpecs


class Validation(CompositeStep):
    def __init__(self) -> None:
        super().__init__(
            name="validation",
            children=[
                EvaluateSpecs(),
            ],
        )
