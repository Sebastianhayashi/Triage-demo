# WPML Support Triage MVP – System Overview

This document explains how the repository fits together, the execution flow from a user query to the structured JSON response, and how each folder collaborates with the rest of the system.

## How the system works (end-to-end)

```
User query
   │
   ▼
RuleClassifier (configs/rules.yaml)
   │  └─ Normalizes text, scores rule signals, selects category + confidence
   ▼
TfidfRetriever (artifacts/tfidf.joblib built from data/cases.cleaned.jsonl)
   │  └─ Vectorizes query, finds top-K similar cases, returns citations
   ▼
ActionPlanner (configs/playbooks.yaml)
   │  └─ Selects per-category or default next questions + diagnostic steps
   ▼
Pipeline orchestrator
   │  └─ Assembles schema-validated JSON with meta versions + timestamps
   ▼
CLI (`python src/cli.py "..."`) prints the final structured JSON
```

Key properties:
- **Deterministic**: No external services or LLM calls; everything is local, rules-based, and TF–IDF driven.
- **Config-driven**: Taxonomy/rules/playbooks are versioned YAML (JSON fallbacks) so updates are traceable and reproducible.
- **Reproducible outputs**: `meta.rules_version` and `meta.index_version` capture the config/index versions used at inference time.

## What lives where
- **configs/** – category taxonomy, rule signals, and action playbooks that drive classification and guidance.
- **data/** – cleaned WPML available solutions used to build the retrieval index.
- **artifacts/** – generated TF–IDF index (`tfidf.joblib`) produced by the build script (ignored by git).
- **scripts/** – maintenance/utility scripts; currently the offline TF–IDF index builder.
- **src/** – all runtime code (pipeline modules and CLI entrypoint).
- **tests/** – smoke coverage to ensure the pipeline produces schema-compliant output with citations and action plans.

## Dependency graph at a glance
- `scripts/build_index.py` reads **data/cases.cleaned.jsonl** and writes **artifacts/tfidf.joblib**.
- `src/triage/pipeline.py` loads **configs/rules.yaml**, **configs/playbooks.yaml**, and **artifacts/tfidf.joblib** to wire the classifier, retriever, and action planner.
- `src/cli.py` calls the pipeline and prints the `PipelineOutput` JSON.
- `tests/test_pipeline_smoke.py` spins up the default pipeline, builds the index if missing, and validates output fields.

## Updating or extending
- Adjust category boundaries or detection signals by editing `configs/taxonomy.yaml` and `configs/rules.yaml` (bump their `version` values to keep meta tracking useful).
- Refine action templates in `configs/playbooks.yaml` to collect better information or offer sharper diagnostics.
- Rebuild the index after changing the dataset (`python scripts/build_index.py`) so the retriever stays in sync with `data/cases.cleaned.jsonl`.
