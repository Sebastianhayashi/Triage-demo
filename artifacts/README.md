# artifacts/

Holds generated files that are created locally and ignored by git. The primary output is the TF–IDF index built from the cleaned WPML cases dataset.

- **tfidf.joblib** (generated): produced by `scripts/build_index.py` using `data/cases.cleaned.jsonl`. It packages the fitted vectorizer, sparse matrix, and metadata (including `index_version`).
- Why generated: the index depends on local build steps and may change when data or vectorizer parameters change, so it is kept out of version control to avoid stale binaries.

If the index is missing, the pipeline loader will ask you to run the build script before executing the CLI or tests.
