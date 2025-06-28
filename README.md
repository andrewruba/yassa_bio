# yassa_bio

**yassa_bio** is an open-source bioanalytical pipeline. Starting with ELISA and other ligand-binding assays (LBA), it is designed to expand into a universal engine for plate-based and chromatographic assays. The library delivers regulatory-grade curve-fitting, quality-control, validation metrics and automated reporting that suit academic labs, CROs and regulated industry environments alike.

• **For academic & core labs:** easy-to-install Python package, clear APIs, Jupyter-ready helpers and rich PDF/HTML reports let you move from raw plate files to publishable figures in minutes.

• **For pharma, biotech & CROs:** built around ICH M10, U.S. FDA Bioanalytical Method Validation (BMV 2018) and USP ⟨1225⟩ guidance—so critical parameters (accuracy/precision, parallelism, dilution linearity, SST, carry-over, etc.) are automatically calculated and flagged.

## Folder structure

```
yassa-bio/
├── pyproject.toml
├── LICENSE                 ← Apache-2.0 text
├── README.md
├── yassa_bio/
│   ├── __init__.py         ← version, public re-exports
│   ├── cli.py              ← Typer-based command-line entry
│   ├── config/
│   │   ├── __init__.py
│   │   └── schemas.py      ← Pydantic models (ElisaAnalysisConfig, etc.)
│   ├── io/
│   │   ├── __init__.py
│   │   └── loaders.py      ← plate-reader CSV/XLS parsers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── curves.py       ← 4-PL/5-PL, inverse, weighting
│   │   ├── qc.py           ← calculations for CV, accuracy, SST, ICH/USP rules
│   │   └── pipeline.py     ← light pipeline/orchestrator
│   ├── report/
│   │   ├── __init__.py
│   │   └── render.py       ← HTML/PDF report builder
│   └── datasets/           ← (optional) small sample plates for unit tests
└── tests/
    ├── __init__.py
    ├── test_curves.py
    └── test_qc.py
```

## Developer setup (Poetry)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/yassa_bio.git
cd yassa_bio

# 2. Ensure Poetry is available (once per machine)
pipx install poetry   # or brew install poetry

# 3. Install deps & create the project-scoped venv
poetry install

# 4. Activate the venv *or* prefix with `poetry run`
poetry shell          # optional – drops you inside the venv
# …or…
poetry run pytest -q  # runs any command inside the env

# 5. Install the pre-commit hook (auto-runs ruff/black/mypy)
poetry run pre-commit install
```

### Typical workflow

1. `git checkout -b feature/my-cool-thing`
2. Hack away 🛠️

   - files live under `src/yassa_bio/…`

3. Format & test locally

   ```bash
   poetry run ruff .
   poetry run black .
   poetry run mypy src
   poetry run pytest -q
   ```

4. Commit (the pre-commit hook runs the same checks).
5. Push & open a PR.
   GitHub Actions will lint, type-check, run unit tests, measure coverage and upload to Codecov automatically.
