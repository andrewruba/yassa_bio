from yassa_bio.pipeline.base import Step, PipelineContext


class Acceptance(Step):
    name = "acceptance_criteria"

    def __init__(self, criteria: dict[str, Step]):
        self.criteria = criteria

    def logic(self, ctx: PipelineContext) -> PipelineContext:
        run_type = getattr(ctx.config, "run_type", "default")
        step = self.criteria.get(run_type)
        if not step:
            raise ValueError(f"No route defined for run_type={run_type}")
        return step.run(ctx)
