# tests/

Lightweight verification that the triage pipeline remains runnable and produces schema-compliant output.

- **test_pipeline_smoke.py** — Builds the TF–IDF index on-demand if missing, loads the default pipeline, submits a sample query, and asserts:
  - output matches the schema contract (non-empty action plan, at least one citation when data/index exist)
  - `meta.rules_version` and `meta.index_version` are populated for traceability

Run all tests with:
```bash
pytest -q
```
