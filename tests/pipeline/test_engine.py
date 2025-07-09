from __future__ import annotations
import pytest
import logging

from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.pipeline.base import Step, PipelineContext


class A(Step):
    name = "A"

    def logic(self, ctx):
        ctx.seq.append("A")
        return ctx


class B(Step):
    name = "B"

    def logic(self, ctx):
        ctx.seq.append("B")
        return ctx


class TestPipeline:
    @pytest.mark.usefixtures("caplog")
    def test_pipeline_sequence_order(self, caplog):
        caplog.set_level(logging.INFO)

        ctx = PipelineContext(seq=[])
        pipe = Pipeline([A(), B()], name="my_pipe")

        pipe.run(ctx)

        assert pipe.name == "my_pipe"
        assert ctx.seq == ["A", "B"]
        assert "Starting my_pipe" in caplog.text
        assert "✅ my_pipe finished" in caplog.text
