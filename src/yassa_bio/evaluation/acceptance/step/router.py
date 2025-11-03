from pydantic import BaseModel

from lilpipe.step import Step
from lilpipe.models import PipelineContext


class Acceptance(Step):
    name = "acceptance_criteria"

    def __init__(self, criteria: dict[BaseModel, Step]):
        super().__init__(name=self.name)
        self.criteria = criteria

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        config_type = type(ctx.acceptance_config)
        step = self.criteria.get(config_type)
        if not step:
            raise ValueError(
                f"No route defined for config type: {config_type.__name__}"
            )
        return step.run(ctx)
