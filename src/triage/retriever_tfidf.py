import math
import pickle
from pathlib import Path
from typing import Dict, List

from .rule_classifier import normalize_text


def make_snippet(problem: str, solution: str, max_len: int = 240) -> str:
    text = problem or ""
    if not text:
        text = solution or ""
    snippet = text.strip().replace("\n", " ")
    if len(snippet) > max_len:
        snippet = snippet[: max_len - 3] + "..."
    return snippet


class TfidfRetriever:
    def __init__(self, index_path: Path):
        self.index_path = Path(index_path)
        with self.index_path.open("rb") as f:
            self.index = pickle.load(f)
        self.index_version = self.index.get("index_version", "")

    def search(self, query_text: str, top_k: int = 5) -> List[Dict]:
        q = normalize_text(query_text)
        q_tokens = q.split()
        tf = {}
        for t in q_tokens:
            tf[t] = tf.get(t, 0) + 1
        idf = self.index.get("idf", {})
        q_vec = {t: (c / len(q_tokens)) * idf.get(t, 0.0) for t, c in tf.items() if t in idf}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        scores = []
        for idx, (doc_vec, doc_norm) in enumerate(zip(self.index["doc_vectors"], self.index["doc_norms"])):
            dot = sum(q_vec.get(term, 0.0) * doc_vec.get(term, 0.0) for term in q_vec.keys())
            score = dot / (q_norm * doc_norm)
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:top_k]
        citations: List[Dict] = []
        for i, sc in top:
            m = self.index["meta"][i]
            citations.append(
                {
                    "case_id": m.get("case_id"),
                    "source": m.get("source"),
                    "topic_url": m.get("topic_url"),
                    "title": m.get("title", ""),
                    "forum": m.get("forum", ""),
                    "snippet": make_snippet(m.get("problem", ""), m.get("solution", "")),
                    "score": float(sc),
                }
            )
        return citations
