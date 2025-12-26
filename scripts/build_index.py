import argparse
import json
import math
import pickle
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from triage.rule_classifier import normalize_text  # noqa: E402


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def build_index(cases_path: Path, out_path: Path):
    cases = list(load_jsonl(cases_path))
    texts = [normalize_text(c.get("analysis_text", "")) for c in cases]
    meta = [
        {
            "case_id": c.get("case_id"),
            "source": c.get("source"),
            "topic_url": c.get("topic_url"),
            "title": c.get("title", ""),
            "forum": c.get("forum", ""),
            "problem": c.get("problem", ""),
            "solution": c.get("solution", ""),
        }
        for c in cases
    ]

    doc_tokens = [t.split() for t in texts]
    df_counter = Counter()
    for tokens in doc_tokens:
        df_counter.update(set(tokens))

    total_docs = len(doc_tokens)
    idf = {term: math.log((total_docs + 1) / (df + 1)) + 1 for term, df in df_counter.items()}

    doc_vectors = []
    doc_norms = []
    for tokens in doc_tokens:
        if not tokens:
            doc_vectors.append({})
            doc_norms.append(1.0)
            continue
        tf = Counter(tokens)
        vec = {term: (count / len(tokens)) * idf.get(term, 0.0) for term, count in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        doc_vectors.append(vec)
        doc_norms.append(norm)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        pickle.dump(
            {
                "idf": idf,
                "doc_vectors": doc_vectors,
                "doc_norms": doc_norms,
                "meta": meta,
                "index_version": f"tfidf@cases.cleaned.{len(cases)}",
            },
            f,
        )



def main():
    parser = argparse.ArgumentParser(description="Build TF-IDF index for WPML triage")
    parser.add_argument(
        "--cases",
        type=Path,
        default=BASE_DIR / "data" / "cases.cleaned.jsonl",
        help="Path to cleaned cases JSONL file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=BASE_DIR / "artifacts" / "tfidf.joblib",
        help="Output path for the index joblib",
    )
    args = parser.parse_args()

    build_index(args.cases, args.out)
    print(f"Index built at {args.out} from {args.cases}")


if __name__ == "__main__":
    main()
