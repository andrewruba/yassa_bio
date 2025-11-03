import pytest
from pydantic import BaseModel
from lilpipe.step import Step
from lilpipe.models import PipelineContext
from yassa_bio.evaluation.acceptance.step.router import Acceptance


class ConfigA(BaseModel):
    val: int = 1


class ConfigB(BaseModel):
    val: str = "ok"


class DummyStep(Step):
    name = "dummy"

    def __init__(self) -> None:
        super().__init__(name=self.name)

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        ctx.executed = True
        return ctx


class TestRouter:
    def test_acceptance_routes_correct_step(self):
        ctx = PipelineContext(acceptance_config=ConfigA())
        router = Acceptance(criteria={ConfigA: DummyStep()})
        result = router.run(ctx)
        assert result.executed is True
        assert result.step_meta["acceptance_criteria"]["status"] == "ok"

    def test_acceptance_missing_route_raises(self):
        ctx = PipelineContext(acceptance_config=ConfigB())
        router = Acceptance(criteria={ConfigA: DummyStep()})
        with pytest.raises(
            ValueError, match="No route defined for config type: ConfigB"
        ):
            router.run(ctx)

    def test_acceptance_with_multiple_routes(self):
        ctx = PipelineContext(acceptance_config=ConfigB())
        router = Acceptance(criteria={ConfigA: DummyStep(), ConfigB: DummyStep()})
        result = router.run(ctx)
        assert result.executed is True

    def test_acceptance_config_missing(self):
        ctx = PipelineContext()
        router = Acceptance(criteria={ConfigA: DummyStep()})
        with pytest.raises(AttributeError):
            router.run(ctx)
