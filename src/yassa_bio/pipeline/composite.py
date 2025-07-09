from __future__ import annotations
import logging
from typing import Iterable
from yassa_bio.pipeline.base import Step, PipelineContext

log = logging.getLogger(__name__)

_INDENT = "    "


class CompositeStep(Step):
    """
    Behaves like a normal Step but delegates work to child-steps.

    Console output:
        ▶ ingest
            • resolve_files
            • load_blocks
            • map_signals
        ✓ ingest
    """

    def __init__(self, name: str, children: Iterable[Step]):
        self.name = name
        self.children = list(children)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        return self._run_children(ctx, depth=1)

    def _run_children(self, ctx: PipelineContext, depth: int) -> PipelineContext:
        indent = _INDENT * depth
        log.info("%s▶️  %s", indent, self.name)

        for child in self.children:
            if isinstance(child, CompositeStep):
                ctx = child._run_children(ctx, depth + 1)
            else:
                log.info("%s%s• %s", indent, _INDENT, child.name)
                ctx = child.run(ctx)

        log.info("%s✅ %s", indent, self.name)
        return ctx
