# AGENTS.md

## Project Purpose

`yassa_bio` is the deterministic analysis engine for bioanalytical assay workflows, starting with ELISA/LBA-style plate-based assays. Keep this repository focused on validated data ingestion, typed method/config schemas, reproducible processing, curve fitting, acceptance evaluation, and auditable run outputs.

LLM orchestration, SOP parsing, enterprise UI, authentication, signatures, dashboards, and workflow management should be treated as separate layers that call into this engine. Do not build those features into this repo unless explicitly requested.

## Repository Shape

- `src/yassa_bio/schema/`: Pydantic models for layouts, analysis config, and acceptance criteria.
- `src/yassa_bio/io/`: raw CSV/Excel reader utilities.
- `src/yassa_bio/evaluation/analysis/`: preprocessing and curve-fit pipeline steps plus numerical engines.
- `src/yassa_bio/evaluation/acceptance/`: acceptance criteria routing and evaluators.
- `src/yassa_bio/evaluation/run.py`: current programmatic pipeline entry point.
- `src/yassa_bio/core/`: shared model, enum, typing, and registry helpers.
- `tests/`: unit tests for schemas, IO, engines, and step behavior.
- `TASKLIST.md`: prioritized engine-hardening task list.

## Current Architectural Direction

The engine should expose a constrained set of deterministic primitives. External tools, including LLM-based SOP organizers, should generate typed configs/specs that this engine validates and executes.

Preferred direction:

- Schema-first method/config definitions.
- Explicit built-in primitive registration.
- Typed results instead of loose dictionaries.
- Row-level provenance from raw data through final results.
- Reproducible, serializable run records.
- Reference-tested numerical behavior.
- Audit-friendly event metadata for every meaningful transformation.

## Important Known Issues

- Built-in registry population currently depends on import side effects. A fresh import of `yassa_bio.evaluation.run` does not register all built-in analysis and acceptance plugins.
- `evaluation/run.py` currently lacks direct test coverage.
- Outlier detection currently flags rows but downstream behavior is not clearly enforced.
- Signal normalization needs review; it should not normalize signal using calibration concentration values.
- Back-calculation and acceptance should clearly distinguish transformed-space calculations from original concentration-space reporting.
- Acceptance outputs are currently loose dictionaries and should become typed result models.
- Mypy is present but not enforced in CI yet.

## Development Workflow

Use the existing package style and keep changes scoped. Prefer small, explicit engine improvements over broad refactors.

Before making code changes:

- Inspect relevant source and tests.
- Check for existing patterns before introducing new abstractions.
- Preserve user changes in the working tree.

Useful commands:

```bash
poetry run pytest
poetry run ruff check .
poetry run black --check .
poetry run mypy src/
```

Current expected state:

- `poetry run pytest` should pass.
- `poetry run ruff check .` should pass.
- `poetry run black --check .` should pass.
- `poetry run mypy src/` may fail until the typing baseline is cleaned up.

## Coding Guidelines

- Prefer Pydantic models for structured inputs, configs, and results.
- Avoid adding stringly typed result dictionaries for new behavior.
- Keep numerical behavior deterministic and testable.
- Add tests for every behavior change.
- Use explicit errors for invalid scientific/data conditions instead of silent coercion.
- Preserve raw data provenance whenever data is transformed or summarized.
- Do not add enterprise features to this engine unless requested.
- Do not add LLM/SOP organizer code to this engine unless requested.

## Response Preference

For any response that involved code changes, include a suggested commit message. Do not commit changes unless the user explicitly asks.
