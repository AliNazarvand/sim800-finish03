# Installation Guide

Create a Python 3.11+ environment and install the project in editable mode:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

Run the quality checks with `pytest`, `ruff check src tests scripts`, and `mypy src`. To rebuild data from the external read-only datasheet clone, set its local path in `scripts/build_products.py` or adapt `DATASHEETS`, then run `PYTHONPATH=src python scripts/build_products.py`.
