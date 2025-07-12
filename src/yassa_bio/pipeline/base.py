from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable
import time
import json
import hashlib
import logging
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


def _deep_hash(obj: Any) -> str:
    """SHA-256 digest of *anything* serialisable."""

    def _default(o):
        try:
            return o.model_dump()
        except AttributeError:
            return repr(o)

    return hashlib.sha256(
        json.dumps(obj, default=_default, sort_keys=True).encode()
    ).hexdigest()


class PipelineContext(BaseModel):
    step_meta: Dict[str, Any] = Field(
        default_factory=dict, description="Per-step diagnostics and cache metadata."
    )
    needs_rerun: bool = Field(
        False,
        description=(
            "Set by a step to request a brand-new pipeline pass after the current "
            "one finishes."
        ),
    )
    abort_pass: bool = Field(
        False,
        description=(
            "Set by a step to abort the remainder of the current pass early. "
        ),
    )
    abort_run: bool = Field(
        False,
        description=(
            "Set by a step to terminate the entire pipeline run after the current pass."
        ),
    )

    model_config = {"extra": "allow"}


class Step(ABC):
    """
    Sub-classes **only need to implement logic()**.

    Optional knobs:
      • fingerprint_keys: Iterable[str] – ctx attributes to hash for cache-skip
    """

    name: str = "<unnamed>"
    fingerprint_keys: Iterable[str] | None = None

    def run(self, ctx: PipelineContext) -> PipelineContext:
        meta = ctx.step_meta.setdefault(self.name, {})

        fp = self._fingerprint(ctx)
        if (
            fp is not None
            and meta.get("input_hash") == fp
            and meta.get("status") == "ok"
        ):
            log.info("⤵  Skipping %s (cache hit)", self.name)
            return ctx

        meta["input_hash"] = fp
        t0 = time.perf_counter()

        try:
            ctx = self.logic(ctx)
            meta["status"] = "ok"
        except Exception as exc:
            meta.update(status="error", error=str(exc))
            raise
        finally:
            meta["duration"] = round(time.perf_counter() - t0, 3)
            log.info("⏱️  %s finished in %.3f s", self.name, meta["duration"])

        return ctx

    def _fingerprint(self, ctx: PipelineContext) -> str | None:
        """
        Default: if `fingerprint_keys` is set, hash those ctx attrs.
        Otherwise return None (=> no skipping).
        Override for bespoke fingerprints.
        """
        if self.fingerprint_keys is None:
            return None
        payload = {k: getattr(ctx, k, None) for k in self.fingerprint_keys}
        return _deep_hash(payload)

    @abstractmethod
    def logic(self, ctx: PipelineContext) -> PipelineContext: ...
