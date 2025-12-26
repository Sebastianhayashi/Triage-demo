# WPML Support Triage MVP

This repository implements a minimal reproducible pipeline that takes a user support query and returns structured triage JSON including rule-based categorization, TF–IDF evidence retrieval, and a template-driven action plan.

## Requirements
- Python 3.9+ (standard library only; no extra dependencies required)
- The cleaned WPML available solutions dataset at `data/cases.cleaned.jsonl` (already provided)

## Project layout
- `ARCHITECTURE.md` — end-to-end system overview, dependency graph, and guidance on how folders collaborate.
- `configs/` — taxonomy, rule, and action playbook YAMLs (JSON fallbacks exist alongside them).
- `data/cases.cleaned.jsonl` — cleaned cases used to build the retrieval index.
- `scripts/build_index.py` — offline TF–IDF index builder.
- `artifacts/` — generated TF–IDF index artifact (ignored by git; build locally).
- `src/triage/` — pipeline modules (schema, rule classifier, retriever, action planner, orchestration).
- `src/cli.py` — CLI entry point for one-shot triage.
- `tests/` — smoke test ensuring pipeline output matches the expected schema.

## Quick start
1. **Create virtual environment (optional but recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Build the TF–IDF index** (writes `artifacts/tfidf.joblib`)
   ```bash
   python scripts/build_index.py
   ```
   You can override input/output paths, for example:
   ```bash
   python scripts/build_index.py --cases data/cases.cleaned.jsonl --out artifacts/tfidf.joblib
   ```

3. **Run the triage CLI**
   ```bash
   python src/cli.py "Translation editor does not open for WooCommerce products"
   ```
   - The CLI prints the structured JSON response.
   - Use `--base /path/to/repo` if running from a different working directory.

## Testing
Run the smoke test to verify the end-to-end pipeline. The test will auto-build the TF–IDF index if it is missing.
```bash
pytest -q
```

## Configuration
- Update taxonomy/categories in `configs/taxonomy.yaml`.
- Tune rule weights and thresholds in `configs/rules.yaml`.
- Adjust action plans in `configs/playbooks.yaml` (default plus per-category templates).

## Notes
- The pipeline is deterministic and uses only the provided rules and TF–IDF similarity; there is no LLM dependency.
- `meta.rules_version` and `meta.index_version` in outputs track the config and index versions for reproducibility.
