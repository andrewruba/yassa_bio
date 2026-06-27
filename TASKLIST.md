# yassa_bio Engine Task List

This repo should stay focused on the deterministic analysis engine: validated data structures, reproducible execution, numerical correctness, and auditable outputs. LLM orchestration, enterprise UI, auth, signatures, and workflow management should live in separate products or packages that call into this engine.

## Guiding Principle

The engine should make it difficult to produce an invalid result and easy to explain exactly how a valid result was produced.

## 0. Immediate Correctness Fixes

- [ ] Add an end-to-end smoke test that imports only `yassa_bio.evaluation.run.run` in a fresh process and runs a minimal valid LBA analysis.
- [ ] Fix registry bootstrap so all built-in readers, preprocessing rules, transforms, weighting functions, curve models, and acceptance evaluators are registered before `run()` executes.
- [ ] Decide and implement the outlier policy:
  - flag only
  - exclude from curve fit
  - exclude from acceptance
  - require explicit analyst approval
- [ ] Fix signal normalization so signal normalization uses calibration signal values, not concentration values.
- [ ] Clarify transformed-space versus original-space calculations for curve fitting and back-calculation.
- [ ] Ensure back-calculated concentrations and acceptance accuracy are reported on the original concentration scale with units.
- [ ] Add fail-fast checks for non-finite values after transforms, weighting, fitting, and back-calculation.
- [ ] Replace silent numeric coercion of raw reader values with explicit error reporting for invalid cells.

## 1. Data Ingestion and Layout

- [ ] Add row-level provenance columns to materialized plate data:
  - `plate_id`
  - source file path or URI
  - source file content hash
  - sheet index
  - parser name/version
  - raw row/column
  - well ID
- [ ] Validate that each `PlateLayout` has no duplicate well IDs.
- [ ] Validate that each `PlateLayout` has no duplicate `(file_row, file_col)` raw positions.
- [ ] Validate well IDs against the declared plate format.
- [ ] Validate file positions against the actual raw file shape before extracting values.
- [ ] Add support for reader-specific options through typed schemas rather than loose `**kwargs`.
- [ ] Add golden-file tests for representative CSV and Excel exports from real plate-reader formats.
- [ ] Add a stable `RawDataFingerprint` model for reproducibility checks.

## 2. Schema and Method Definition

- [ ] Introduce a top-level `LBAMethod` or `PipelineSpec` schema that bundles:
  - layout definition
  - preprocessing config
  - curve-fit config
  - acceptance criteria
  - engine version
  - method version
  - units
  - validation status
- [ ] Make config/result schemas serializable to canonical JSON.
- [ ] Add schema version fields and migration strategy for future breaking changes.
- [ ] Replace mutable default model instances with `Field(default_factory=...)`.
- [ ] Add explicit unit validation for concentration and signal-related fields.
- [ ] Define allowed assay families and keep LBA-specific fields separate from generic plate-analysis fields.
- [ ] Define stable reason codes for validation failures and acceptance failures.

## 3. Preprocessing Engine

- [ ] Make every preprocessing step emit a structured audit/event record.
- [ ] Preserve before/after summary statistics for blank subtraction, normalization, exclusion, and outlier detection.
- [ ] Track user-specified exclusions separately from algorithmic exclusions.
- [ ] Require exclusion reasons for all user-specified exclusions.
- [ ] Add tests for blank subtraction when blank wells are missing, invalid, excluded, or non-finite.
- [ ] Add tests for normalization behavior with increasing and decreasing signal curves.
- [ ] Add tests showing how outlier flags affect, or do not affect, downstream fit and acceptance.

## 4. Curve Fitting and Numerical Engine

- [ ] Add fit diagnostics:
  - convergence status
  - optimizer message
  - parameter covariance
  - residuals
  - weighted residuals
  - goodness-of-fit metrics
- [ ] Add bounds and initialization strategies that are explicit in the config/result.
- [ ] Add monotonicity and invertibility checks for fitted calibration curves.
- [ ] Add robust handling for divide-by-zero and negative values in weighting and transforms.
- [ ] Add tests for 4PL, 5PL, and linear fits against known reference datasets.
- [ ] Add tests for failed/non-convergent fits and verify structured errors.
- [ ] Decide whether transformations are model inputs or reporting-only transformations, then document and enforce that choice.
- [ ] Store fitted model results in typed models instead of callables alone.

## 5. Acceptance Evaluation

- [ ] Replace loose acceptance result dictionaries with typed Pydantic result models.
- [ ] Add calculation metadata to each acceptance result:
  - threshold
  - observed value
  - pass/fail
  - reason code
  - source rows
  - formula name/version
- [ ] Clarify calibration acceptance semantics around `pass_fraction` and failing levels.
- [ ] Add QC precision/CV evaluation if README continues to claim QC accuracy/precision.
- [ ] Add explicit LLOQ/ULOQ handling for calibration and QC rules.
- [ ] Add acceptance tests aligned to ICH M10/FDA BMV examples where possible.
- [ ] Add a rerun/refit history model that records every dropped level and every fit attempt.
- [ ] Prevent infinite or ambiguous reruns with explicit rerun policy and structured termination reasons.

## 6. Execution Context and Run Records

- [ ] Add a typed `RunRecord` output that contains:
  - input fingerprints
  - method/config hash
  - engine package version
  - dependency versions
  - step metadata
  - fit result
  - acceptance result
  - warnings/errors
- [ ] Make pipeline definitions versioned and serializable instead of relying only on a module-level `pipe`.
- [ ] Ensure all random or optimizer-dependent behavior is reproducible or recorded.
- [ ] Add canonical output serialization for reports and downstream APIs.
- [ ] Add a deterministic hash for each run result.
- [ ] Add tests that re-run the same input/config and assert identical serialized outputs.

## 7. Registry and Extension System

- [ ] Add a built-in plugin bootstrap module with explicit imports.
- [ ] Add registry introspection APIs for available readers, transforms, models, weighting rules, and acceptance evaluators.
- [ ] Add metadata to registered functions:
  - name
  - version
  - domain
  - expected inputs
  - output schema
  - validation status
- [ ] Decide whether external plugins are supported in the core engine or only in downstream products.
- [ ] Add tests that detect missing registrations for every enum value.

## 8. Testing and Quality Gates

- [ ] Add end-to-end tests for `run()` using real test data.
- [ ] Add property-style tests for schema validation and numerical edge cases.
- [ ] Add regression tests for known bug cases.
- [ ] Add coverage threshold enforcement for the package and specifically for `evaluation/run.py`.
- [ ] Remove `|| true` from the mypy CI step once the baseline is cleaned up.
- [ ] Add pandas/scipy stubs or mypy config so type checking is meaningful.
- [ ] Add stricter type checks around nullable context fields.
- [ ] Keep `ruff`, `black --check`, and `pytest` as required gates.

## 9. Documentation

- [ ] Update README project layout so `core/` is described as shared infrastructure, not curve fitting.
- [ ] Add a validated-engine architecture document.
- [ ] Add a data-flow diagram:
  - raw file
  - layout
  - normalized tabular data
  - preprocessing
  - fit
  - acceptance
  - run record
- [ ] Add minimal working examples that actually execute in CI.
- [ ] Add a "Scope of Core Engine" section that excludes LLM orchestration and enterprise workflow features.
- [ ] Add a "Validation Status" section distinguishing implemented, tested, reference-verified, and externally validated features.

## 10. Suggested Milestones

- [ ] Milestone 1: Fresh-process `run()` works end to end with typed outputs.
- [ ] Milestone 2: Ingestion provenance and run records are stable.
- [ ] Milestone 3: Curve fitting and acceptance are reference-tested.
- [ ] Milestone 4: Engine outputs are canonical, hashable, and reproducible.
- [ ] Milestone 5: The package can serve as a constrained execution backend for an external SOP/LLM organizer.
