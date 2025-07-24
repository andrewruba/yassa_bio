from yassa_bio.pipeline.base import Step
from yassa_bio.core.registry import get
from yassa_bio.evaluation.context import LBAContext
from yassa_bio.schema.acceptance.analytical.spec import (
    LBAAnalyticalAcceptanceCriteria,
)
from yassa_bio.schema.acceptance.validation.spec import (
    LBAValidationAcceptanceCriteria,
)


class EvaluateSpecs(Step):
    name = "evaluate_specs"
    fingerprint_keys = None

    def logic(self, ctx: LBAContext) -> LBAContext:
        crit: LBAAnalyticalAcceptanceCriteria | LBAValidationAcceptanceCriteria = (
            ctx.acceptance_criteria
        )
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
