# data/

Holds the cleaned WPML Available Solutions dataset used for retrieval.

- **cases.cleaned.jsonl** — Each line is a cleaned case containing `analysis_text` (title + problem), forum metadata, problem/solution text, and stable IDs. Cleaning removed noisy titles and standardized fields so TF–IDF indexing is consistent.

The retrieval index (`artifacts/tfidf.joblib`) is built directly from this file by `scripts/build_index.py`. If you swap in a new dataset or perform additional cleaning, rebuild the index to keep search results aligned with the data.
