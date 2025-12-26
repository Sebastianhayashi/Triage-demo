# src/triage/

Core pipeline building blocks. These modules collaborate to turn a raw support query into the structured triage JSON defined in `schema.py`.

- **schema.py** — Dataclass-based schema for the pipeline output (query, triage result with signals/confidence, citations, action plan, meta). Provides `dict()` and `json()` helpers plus `parse_obj` for validation.
- **rule_classifier.py** — Implements keyword/regex scoring using `configs/rules.yaml`. Normalizes text, aggregates matched signals, applies thresholds, and returns `{category, confidence, signals}`. Confidence uses the margin between the top two scores; low scores/confidence fall back to `other`.
- **retriever_tfidf.py** — Loads `artifacts/tfidf.joblib`, transforms the query with the stored vectorizer, computes cosine similarity against the matrix, and emits top-K citations with metadata and snippets.
- **action_plan.py** — Selects template next questions and diagnostic steps from `configs/playbooks.yaml`. Falls back to the default playbook when confidence is low.
- **pipeline.py** — Orchestrator that wires classifier, retriever, and planner; stamps versions (`rules_version`, `index_version`) and timestamps; returns `PipelineOutput`. Includes `load_default_pipeline()` to bootstrap all components using repo-relative paths.

Typical flow inside `Pipeline.run()`:
1. Classify query → category, confidence, matched signals.
2. Retrieve top-K similar cases → citations with scores.
3. Choose action plan template → next questions + diagnostic steps.
4. Assemble `PipelineOutput` with schema version, meta, and serialized-friendly objects.
