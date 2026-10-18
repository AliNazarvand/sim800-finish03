# Usage

```bash
python -m pip install -e '.[dev]'
python scripts/validate_dataset.py
python -m sim800_tools.cli diff old.jsonl new.jsonl --output data/diffs/commands.json
```

The driver accepts any transport implementing `write(bytes)` and `read_until(bytes, timeout)`, so serial, USB, and test doubles remain interchangeable.
