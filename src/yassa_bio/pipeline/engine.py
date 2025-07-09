from __future__ import annotations
import logging
from typing import Sequence
from yassa_bio.pipeline.base import Step, PipelineContext

log = logging.getLogger(__name__)


class Pipeline:
    """
    Holds an ordered list of Step instances and runs them sequentially.
    """

    def __init__(self, steps: Sequence[Step], name: str = "pipeline"):
        self.steps = list(steps)
        self.name = name

    def run(self, ctx: PipelineContext) -> PipelineContext:
        log.info("▶️  Starting %s with %d steps", self.name, len(self.steps))
        for step in self.steps:
            log.info("  • %s", step.name)
            ctx = step.run(ctx)
        log.info("✅ %s finished", self.name)
        return ctx
