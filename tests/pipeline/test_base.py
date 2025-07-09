from __future__ import annotations
import pytest
import logging
from pydantic import BaseModel

from yassa_bio.pipeline.base import Step, PipelineContext, _deep_hash


class PlainModel(BaseModel):
    a: int
    b: list[int]


class PlainObj:
    def __init__(self, x):
        self.x = x


class TestDeepHash:
    @pytest.mark.parametrize(
        ("obj1", "obj2"),
        [
            ({"a": 1, "b": [2, 3]}, 0),
            ({"a": 1, "b": [2, 3]}, "foo"),
            (0, "foo"),
            (PlainModel(a=1, b=[2, 3]), PlainModel(a=2, b=[2, 3])),
            (PlainObj(x=1), PlainObj(x=2)),
        ],
    )
    def test_deep_hash_diff_input_are_diff_hash(self, obj1, obj2):
        assert _deep_hash(obj1) != _deep_hash(obj2)

    def test_deep_hash_same_input_same_hash(self):
        obj = {"x": [1, 2, 3]}
        assert _deep_hash(obj) == _deep_hash(obj)

        model = PlainModel(a=5, b=[9, 9])
        assert _deep_hash(model) == _deep_hash(model)

        obj = PlainObj(x=1)
        assert _deep_hash(obj) == _deep_hash(obj)


class AlwaysRun(Step):
    """Runs every call; increments ctx.foo."""

    name = "always"

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        ctx.foo = getattr(ctx, "foo", 0) + 1
        return ctx


class SkipOnBar(Step):
    """
    Doubles ctx.bar.  Because 'bar' is fingerprinted, the step
    will execute again whenever ctx.bar changes.
    """

    name = "skip_on_bar"
    fingerprint_keys = ("bar",)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        ctx.bar *= 2
        return ctx


class Cacheable(Step):
    """
    Uses 'control' as fingerprint key but never mutates it,
    so second call should hit the cache and be skipped.
    """

    name = "cacheable"
    fingerprint_keys = ("control",)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        ctx.calls = getattr(ctx, "calls", 0) + 1
        return ctx


class TestStep:
    def test_always_runs(self):
        ctx = PipelineContext(foo=0)
        step = AlwaysRun()

        ctx = step.run(ctx)
        ctx = step.run(ctx)
        assert ctx.foo == 2

    def test_no_skip_when_fingerprint_changes(self):
        ctx = PipelineContext(bar=2)
        step = SkipOnBar()

        ctx = step.run(ctx)  # 2 → 4
        ctx = step.run(ctx)  # 4 → 8
        assert ctx.bar == 8

    @pytest.mark.usefixtures("caplog")
    def test_cache_hit_skips_step(self, caplog):
        caplog.set_level(logging.INFO)

        ctx = PipelineContext(control="CONST")
        step = Cacheable()

        ctx = step.run(ctx)  # executes, calls = 1
        ctx = step.run(ctx)  # should skip
        assert ctx.calls == 1
        assert "Skipping cacheable" in caplog.text

    def test_error_status_recorded(self):
        class Boom(Step):
            name = "boom"

            def logic(self, ctx):
                raise ValueError("bang")

        ctx = PipelineContext()
        with pytest.raises(ValueError):
            Boom().run(ctx)

        meta = ctx.step_meta["boom"]
        assert meta["status"] == "error"
        assert "bang" in meta["error"]
