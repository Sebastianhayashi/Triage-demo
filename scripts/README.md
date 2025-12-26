# scripts/

Utility and maintenance scripts that support the runtime pipeline.

- **build_index.py** — Offline job that reads `data/cases.cleaned.jsonl`, fits a TF–IDF vectorizer over `analysis_text`, and writes `artifacts/tfidf.joblib` containing the matrix, vectorizer, metadata, and `index_version` string. The retriever loads this artifact at runtime.

Typical usage:
```bash
python scripts/build_index.py --cases data/cases.cleaned.jsonl --out artifacts/tfidf.joblib
```
