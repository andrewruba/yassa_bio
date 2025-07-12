from __future__ import annotations
import pytest
import logging

from yassa_bio.pipeline.engine import Pipeline
from yassa_bio.pipeline.base import Step, PipelineContext


class Record(Step):
    """Append own name to ctx.seq so we can inspect execution order."""

    def __init__(self, name: str):
        self.name = name

    def logic(self, ctx: PipelineContext):
        ctx.seq.append(self.name)
        return ctx


class FlagSetter(Record):
    """Same as Record but toggles a Boolean flag on the context."""

    def __init__(self, name: str, flag: str):
        super().__init__(name)
        self._flag = flag

    def logic(self, ctx: PipelineContext):
        super().logic(ctx)
        setattr(ctx, self._flag, True)
        return ctx


class OneShotFlagSetter(Record):
    """Sets ctx.<flag> only the first time it runs."""

    def __init__(self, name: str, flag: str):
        super().__init__(name)
        self._flag = flag
        self._done = False

    def logic(self, ctx: PipelineContext):
        super().logic(ctx)
        if not self._done:
            setattr(ctx, self._flag, True)
            self._done = True
        return ctx


class TestPipeline:
    @pytest.mark.usefixtures("caplog")
    def test_pipeline_sequence_order(self, caplog):
        caplog.set_level(logging.INFO)

        steps = [
            Record("first"),
            Record("last"),
        ]
        ctx = PipelineContext(seq=[])
        pipe = Pipeline(steps, name="my_pipe", max_loops=3)
        pipe.run(ctx)

        assert ctx.seq == ["first", "last"]
        assert pipe.name == "my_pipe"
        assert "▶️  my_pipe pass" in caplog.text
        assert "✅  my_pipe finished" in caplog.text

    def test_needs_rerun_triggers_second_pass(self):
        steps = [
            Record("first"),
            OneShotFlagSetter("redo", "needs_rerun"),
            Record("last"),
        ]
        ctx = PipelineContext(seq=[])
        Pipeline(steps, max_loops=3).run(ctx)

        assert ctx.seq == ["first", "redo", "last", "first", "redo", "last"]

    def test_abort_pass_skips_remaining_steps(self):
        steps = [
            FlagSetter("killer", "abort_pass"),
            Record("should_not_run"),
        ]
        ctx = PipelineContext(seq=[])
        Pipeline(steps).run(ctx)

        assert ctx.seq == ["killer"]

    def test_abort_pass_allows_rerun_but_skips_rest_of_pass(self):
        steps = [
            OneShotFlagSetter("redo", "needs_rerun"),
            FlagSetter("stop_now", "abort_pass"),
            Record("never_seen"),
        ]
        ctx = PipelineContext(seq=[])
        Pipeline(steps, max_loops=5).run(ctx)

        assert ctx.seq == ["redo", "stop_now", "redo", "stop_now"]

    def test_abort_run_terminates_pipeline(self):
        steps = [
            FlagSetter("panic", "abort_run"),
            Record("never_reached"),
        ]
        ctx = PipelineContext(seq=[])
        Pipeline(steps).run(ctx)

        assert ctx.seq == ["panic"]

    def test_abort_run_cancels_rerun_completely(self):
        steps = [
            OneShotFlagSetter("redo", "needs_rerun"),
            FlagSetter("panic", "abort_run"),
            Record("never_reached"),
        ]
        ctx = PipelineContext(seq=[])
        Pipeline(steps, max_loops=5).run(ctx)

        assert ctx.seq == ["redo", "panic"]

    def test_exceeding_max_loops_raises(self):
        steps = [
            Record("first"),
            FlagSetter("redo", "needs_rerun"),
            Record("last"),
        ]
        ctx = PipelineContext(seq=[])

        with pytest.raises(RuntimeError, match="exceeded 3 passes"):
            Pipeline(steps, max_loops=3).run(ctx)
