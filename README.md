# sim800-platform — Data Extraction & Platform Roadmap

> Machine-readable extraction from 13 SIM800 PDF files into a queryable dataset.

## Project Goals

1. **Machine-readable extraction from 13 PDF files** stored in `data/raw/`,
   turning them into a queryable dataset.
2. **SIM800 platform planning** on top of TinyGSM + custom layers.

## Repository Structure

sim800-platform/
├── .github/ # GitHub workflows, templates, dependabot, CODEOWNERS
├── data/
│ ├── raw/ # 13 original SimCom PDFs (not committed)
│ ├── extracted/ # Extracted plain text (not committed)
│ └── schemas/ # JSON Schemas + README
├── dataset/ # JSONL output files + README
├── planning/ # Four planning CSV files + README
├── scripts/ # Python scripts (extract / generate / validate)
├── src/ # Source code (driver / adapter / tools)
├── docs/ # Architecture, planning, extraction docs
├── examples/ # Usage examples (ESP32 / STM32 / templates)
├── tests/ # Test suite
└── tools/ # Utility tools
text


## Planning Files

| File | Purpose | Rows |
|---|---|---|
| `A_Project_Backlog.csv` | Software engineering tasks | 10 |
| `B_Data_Product_Catalog.csv` | Data products extracted from PDFs | 4 |
| `A_Project_Dependencies.csv` | Backlog dependency junction table | 12 |
| `B_Data_Product_Dependencies.csv` | Data-product dependency junction table | 4 |

See `docs/PLANNING.md` for column-by-column reference.

## The 13 Identified PDFs

| # | File Name | `doc_id` |
|---|---|---|
| 1 | SIM800 Series_AT Command Manual_V1.01.pdf | `sim800_at_manual_v1.01` |
| 2 | SIM800 Series_AT Command Manual_V1.10.pdf | `sim800_at_manual_v1.10` |
| 3 | SIM800 Series_AT Command Manual_V1.12.pdf | `sim800_at_manual_v1.12` |
| 4 | SIM800_Hardware Design_V1.09.pdf | `sim800_hw_design_v1.09` |
| 5 | SIM800A_Hardware Design_V1.02.pdf | `sim800a_hw_design_v1.02` |
| 6 | SIM800C-DS_Hardware_Design_V1.01.pdf | `sim800c_ds_hw_design_v1.01` |
| 7 | SIM800C_Hardware_Design_V1.02.pdf | `sim800c_hw_design_v1.02` |
| 8 | SIM800F_Hardware Design_V1.05.pdf | `sim800f_hw_design_v1.05` |
| 9 | SIM800H&SIM800L_Hardware Design_V2.02.PDF | `sim800h_sim800l_hw_design_v2.02` |
| 10 | SIM800H_Hardware Design_V2.03.pdf | `sim800h_hw_design_v2.03` |
| 11 | SIM800L_Hardware Design_V1.00.pdf | `sim800l_hw_design_v1.00` |
| 12 | SIM808_Hardware Design_V1.03.pdf | `sim808_hw_design_v1.03` |
| 13 | SIM868_Hardware_Design_V1.00.pdf | `sim868_hw_design_v1.00` |

## Extraction Process

1. **Identify the 13 PDFs** — done ✅
2. **Extract text** — `pdftotext -layout` for text PDFs, `tesseract` for scans.
3. **Extract the first 5 records of `commands.jsonl`** — manually, to establish the format.
4. **Define the JSON Schema** (tol_07) based on those first 5 records.
5. **Bulk generation** — via script or semi-manual.
6. **Validation** — JSON Schema + consistency tests.

**Minimum target was 50 records; current dataset contains 357 command records.**

See `docs/EXTRACTION.md` for the full process.

## Tooling

- **Python 3.11+** with `pyproject.toml` (ruff, mypy, pytest, coverage).
- **Pre-commit hooks** (`.pre-commit-config.yaml`).
- **GitHub Actions**: `lint.yml` (ruff + mypy) and `test.yml` (pytest matrix).
- **Dependabot** for pip and GitHub Actions.

Install dev dependencies:

pip install -e ".[dev]"
pre-commit install
text


## License

- **Code and schemas:** MIT License
- **PDF content:** owned by SimCom
- **Extracted dataset:** until the license status of the PDFs is determined, keep it in a **private repository**.
- **What can be published publicly:** schema, tooling, and extraction scripts — not the extracted content.

## Current Status

- ✅ Planning tables approved
- ✅ Dependency tables approved
- ✅ 13 PDF files identified and stored in `data/raw/` (not committed)
- ✅ 18 JSON Schemas defined under `data/schemas/`
- ✅ Git repository initialized with a clean history
- ✅ Dev infrastructure in place (pyproject, pre-commit, CI)
- ✅ Data extraction complete — 357 command records, 255 error codes, 43 deprecation candidates, 1095 version-matrix rows. All QA Gates PASS. Release v0.1.0 packaged.

**From this point forward: data only.**


## Implemented platform (v0.1.0)

The repository now contains working underscore-named packages: `sim800_driver`, `sim800_adapter`, `sim800_validation`, `sim800_diffing`, and `sim800_tools`. Install with `python3 -m pip install -e '.[dev]'`, validate with `python scripts/validate_dataset.py`, and inspect `ARCHITECTURE.md` for the data flow. The code and schemas use MIT; the external SimCom datasheets retain their original ownership and are excluded from release archives.
