# src/

Runtime code for the triage pipeline, exposing both a CLI entrypoint and modular components.

- **cli.py** — Thin wrapper that loads the default pipeline, accepts a query string, and prints the structured JSON response. Supports `--base` to point at an alternate repo root.
- **triage/** — Core library modules: schema definitions, rule-based classifier, TF–IDF retriever, action planner, and pipeline orchestration. These modules are importable for programmatic use beyond the CLI.

Code in this directory is pure Python with only standard-library dependencies, keeping the MVP easy to run in constrained environments.
