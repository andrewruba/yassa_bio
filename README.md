# yassa_bio

**yassa_bio** is an open-source, validation-ready Python toolkit for bioanalytical assay data—starting with ELISA and other ligand-binding assays (LBA), with a roadmap toward universal support for plate-based and chromatographic assays.

It is built for **scientific rigor**, **automation**, and **regulatory alignment**—targeting labs that need reliable, explainable, and auditable pipelines, from academic cores to pharma and CROs.

---

## Key Features

- ✅ **Curve fitting and back-calculation**: Supports 4PL, 5PL, and linear models with transform, weighting, and outlier handling
- ✅ **ICH M10 / FDA BMV 2018 / USP ⟨1225⟩-based acceptance criteria**
- ✅ **Automated evaluation of**:
  - Calibration fit
  - QC accuracy/precision
  - Carryover
  - Selectivity, specificity
  - Dilution linearity
  - Stability
- ✅ **Flexible schema** for validation and analytical runs using `pydantic` models
- ✅ **Extensible plug-in registry**: Add new evaluators or transform logic via decorators
- ✅ **Rerun-aware pipeline engine**: Smart re-evaluation when calibration levels fail and are dropped
- ✅ **Readable outputs**: Results returned as dicts for use in HTML/PDF reports (planned)

---

## Current Limitations

**This repo is in early alpha. Expect breaking changes.**

Some modules are incomplete or experimental:

- ❌ `parallelism` and `recovery` evaluators and schemas are implemented, but not finalized or externally validated
- ❌ No graphical reports or CLI UX yet—data must be loaded programmatically
- ❌ No built-in loader UI: You must manually specify `PlateLayout` and `WellTemplate` objects to describe the assay design
- ❌ Only handles **one sample matrix per run**; support for multi-matrix batches and plate stitching is planned
- ❌ No real multi-sample evaluation yet (e.g. for parallelism or incurred samples)

---

## Design Philosophy

This library is:

- **Schema-first**: All input/output structures are formalized via `pydantic`, enabling structured config, validation, and API wrapping
- **Composable**: Pipelines consist of atomic steps with a typed shared `Context`, rerunnable after refitting
- **Domain-aligned**: Acceptance steps follow bioanalytical validation standards like ICH M10, FDA BMV 2018, and USP ⟨1225⟩
- **Deployable**: Future enterprise modules (auth, signoff workflows, dashboards) will wrap this open core

---

## Example Usage

```python
from yassa_bio.run import run
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.validation.spec import LBAValidationAcceptanceCriteria

ctx = run(
    batch_data=BatchData(...),
    analysis_config=LBAAnalysisConfig(),
    acceptance_criteria=LBAValidationAcceptanceCriteria(),
)

print(ctx.acceptance_results)
````

See [PlateData](src/yassa_bio/schema/layout/plate.py) and [WellTemplate](src/yassa_bio/schema/layout/well.py) for how to define input formats.

---

## Developer Setup

```bash
git clone https://github.com/your-username/yassa_bio.git
cd yassa_bio

pipx install poetry         # or: brew install poetry
poetry install              # install dependencies
poetry run pre-commit install
poetry run pytest           # run tests
```

---

## Project Layout

```
yassa_bio/
├── pipeline/         ← Core engine: step, pipeline, rerun, dispatch
├── schema/           ← Pydantic models: layout, acceptance, config
├── evaluation/       ← Step logic for acceptance criteria
├── core/             ← Curve fitting, transforms, QC utilities
├── io/               ← Raw data loaders (CSV, Excel)
└── run.py            ← Main entrypoint to run the pipeline
```

---

## Contributing

This is an early-stage open science tool. If you're in pharma, biotech, or academia and would like to collaborate, file an issue or email the maintainer. You can also:

* Fork the repo and open a PR
* Request features or improvements
* Share example plate formats or data

---

## License

Apache 2.0 – free for academic, commercial, and clinical use.

---

## Questions?

Contact \[[ruba.andrew@gmail.com](mailto:ruba.andrew@gmail.com)] or open a GitHub Issue.
