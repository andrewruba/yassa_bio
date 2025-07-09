from __future__ import annotations
import logging
import pytest

from yassa_bio.pipeline.composite import CompositeStep
from yassa_bio.pipeline.base import Step, PipelineContext


class Leaf(Step):
    def __init__(self, name):
        self.name = name

    def logic(self, ctx):
        ctx.visited.append(self.name)
        return ctx


class TestComposite:
    @pytest.mark.usefixtures("caplog")
    def test_composite_nested(self, caplog):
        caplog.set_level(logging.INFO)

        inner = CompositeStep("inner", children=[Leaf("C"), Leaf("D")])
        outer = CompositeStep("outer", children=[Leaf("A"), inner, Leaf("B")])

        ctx = PipelineContext(visited=[])
        outer.run(ctx)

        assert ctx.visited == ["A", "C", "D", "B"]
        log_text = caplog.text
        assert "▶️  outer" in log_text and "✅ outer" in log_text
        assert "▶️  inner" in log_text and "✅ inner" in log_text
