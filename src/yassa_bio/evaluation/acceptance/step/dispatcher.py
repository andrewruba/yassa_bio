from lilpipe.step import Step
from yassa_bio.core.registry import get
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical.spec import (
    LBAAnalyticalAcceptanceCriteria,
)


class EvaluateSpecs(Step):
    name = "evaluate_specs"

    def __init__(self) -> None:
        super().__init__(name=self.name)

    def logic(self, ctx: LBAContext) -> LBAContext:
        crit: LBAAnalyticalAcceptanceCriteria = ctx.acceptance_criteria
        results: dict[str, dict] = {}
        overall = True

        for field_name in crit.__class__.model_fields:
            spec_obj = getattr(crit, field_name)
            spec_cls = type(spec_obj).__name__
            fn = get("acceptance", spec_cls)

            res = fn(ctx, spec_obj)
            results[field_name] = res
            overall &= bool(res["pass"])

        ctx.acceptance_results = results
        history = getattr(ctx, "acceptance_history", [])
        history.append(results)
        ctx.acceptance_history = history
        ctx.acceptance_pass = overall

        return ctx
