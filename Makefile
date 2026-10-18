.PHONY: test validate lint

# The pyproject.toml is the dependency source of truth.
test:
	python -m pytest

validate:
	python scripts/validate_dataset.py

lint:
	ruff check .
