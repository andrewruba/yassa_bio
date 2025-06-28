# yassa_bio
**Enhanced repo description**

**yassa_bio** is an open-source bioanalytical pipeline. Starting with ELISA and other ligand-binding assays (LBA), it is designed to expand into a universal engine for plate-based and chromatographic assays. The library delivers regulatory-grade curve-fitting, quality-control, validation metrics and automated reporting that suit academic labs, CROs and regulated industry environments alike.

• **For academic & core labs:** easy-to-install Python package, clear APIs, Jupyter-ready helpers and rich PDF/HTML reports let you move from raw plate files to publishable figures in minutes.
• **For pharma, biotech & CROs:** built around ICH M10, U.S. FDA Bioanalytical Method Validation (BMV 2018) and USP ⟨1225⟩ guidance—so critical parameters (accuracy/precision, parallelism, dilution linearity, SST, carry-over, etc.) are automatically calculated and flagged.

---

### Suggested GitHub topics

`bioinformatics elisa ligand-binding bioanalytics qc validation ich-m10 usp1225 plate-reader curve-fitting python`

Feel free to add/remove to fit the repo cap (20 tags).


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
