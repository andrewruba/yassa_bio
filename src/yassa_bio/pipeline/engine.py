from __future__ import annotations
import logging
from typing import Sequence

from yassa_bio.pipeline.base import Step, PipelineContext

log = logging.getLogger(__name__)


class Pipeline:
    """
    Holds an ordered list of Step instances and runs them sequentially.
    """

    def __init__(
        self,
        steps: Sequence[Step],
        name: str = "pipeline",
        max_loops: int = 3,
    ):
        self.steps = list(steps)
        self.name = name
        self.max_loops = max_loops

    def _once(self, ctx: PipelineContext) -> PipelineContext:
        log.info("▶️  %s pass", self.name)
        ctx.abort_pass = False
        for step in self.steps:
            ctx = step.run(ctx)
            if ctx.abort_pass or ctx.abort_run:
                break
        return ctx

    def run(self, ctx: PipelineContext) -> PipelineContext:
        loops = 0
        ctx.abort_run = False

        while True:
            ctx.needs_rerun = False
            ctx = self._once(ctx)

            loops += 1

            if ctx.abort_run:
                log.info("🛑  %s aborted after %d pass(es)", self.name, loops)
                break

            if ctx.needs_rerun:
                if loops >= self.max_loops:
                    raise RuntimeError(f"{self.name}: exceeded {self.max_loops} passes")
                log.info("🔄  Re-running %s (pass %d)", self.name, loops + 1)
                continue

            break

        log.info("✅  %s finished after %d pass(es)", self.name, loops)
        return ctx
