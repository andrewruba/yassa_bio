# yassa_bio

![CI](https://github.com/andrewruba/yassa_bio/actions/workflows/ci.yaml/badge.svg)
![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)
[![codecov](https://codecov.io/gh/andrewruba/yassa_bio/branch/main/graph/badge.svg)](https://codecov.io/gh/andrewruba/yassa_bio)

**yassa_bio** is an open-source Python toolkit for bioanalytical assay data, starting with ELISA and other ligand-binding assays (LBA), with a roadmap toward universal support for plate-based and chromatographic assays.

It is built for **scientific rigor**, **automation**, and **regulatory alignment**—targeting labs that need reliable, explainable, and auditable pipelines, from academic cores to pharma and CROs.

---

## Key Features

- ✅ **Curve fitting and back-calculation**: Supports 4PL, 5PL, and linear models with transform, weighting, and outlier handling
- ✅ **ICH M10 / FDA BMV 2018 / USP ⟨1225⟩-based acceptance criteria**
- ✅ **Automated evaluation of**:
  - Calibration fit
  - QC accuracy/precision
- ✅ **Flexible schema** for analytical runs using `pydantic` models
- ✅ **Extensible plug-in registry**: Add new evaluators or transform logic via decorators
- ✅ **Rerun-aware pipeline engine**: Smart re-evaluation when calibration levels fail and are dropped
- ✅ **Readable outputs**: Results returned as dicts

---

## Design Philosophy

This library is:

- **Schema-first**: All input/output structures are formalized via `pydantic`, enabling structured config, validation, and API wrapping
- **Composable**: Pipelines consist of atomic steps with a typed shared `Context`, rerunnable after refitting
- **Domain-aligned**: Acceptance steps follow bioanalytical validation standards like ICH M10, FDA BMV 2018, and USP ⟨1225⟩
- **Deployable**: Enterprise modules (auth, signoff workflows, dashboards) could wrap this open core

---

## Example Usage

```python
from yassa_bio.evaluation.run import run
from yassa_bio.schema.layout.batch import BatchData
from yassa_bio.schema.analysis.config import LBAAnalysisConfig
from yassa_bio.schema.acceptance.analytical.spec import LBAAnalyticalAcceptanceCriteria

ctx = run(
    batch_data=BatchData(...),
    analysis_config=LBAAnalysisConfig(),
    acceptance_criteria=LBAAnalyticalAcceptanceCriteria(),
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
├── schema/           ← Pydantic models: layout, acceptance, config
├── evaluation/       ← Step logic for acceptance criteria
├── core/             ← Curve fitting, transforms, QC utilities
├── io/               ← Raw data loaders (CSV, Excel)
└── run.py            ← Main entrypoint to run the pipeline
```

---

## Contributing

This is an open science tool. If you're in pharma, biotech, or academia and would like to collaborate, file an issue or email the maintainer. You can also:

* Fork the repo and open a PR
* Request features or improvements
* Share example plate formats or data

---

## License

Apache 2.0 – free for academic, commercial, and clinical use.

---

## Questions?

Contact \[[ruba.andrew@gmail.com](mailto:ruba.andrew@gmail.com)] or open a GitHub Issue.
