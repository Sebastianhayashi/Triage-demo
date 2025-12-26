import re
from typing import Dict, List, Tuple

from .schema import Signal


def normalize_text(s: str) -> str:
    s = s or ""
    s = s.replace("…", "...")
    s = s.lower()
    s = " ".join(s.split())
    return s


class RuleClassifier:
    def __init__(self, rules_cfg: Dict):
        self.rules_cfg = rules_cfg
        self.categories = rules_cfg.get("categories", {})
        self.thresholds = rules_cfg.get("thresholds", {})
        self.rules_version = rules_cfg.get("version", "")

    def classify(self, query_text: str) -> Dict:
        q = normalize_text(query_text)

        scored: List[Tuple[str, float, List[Signal]]] = []
        for cat, rule in self.categories.items():
            score = 0.0
            matched: List[Signal] = []

            for kw in rule.get("keywords", []):
                if kw.get("pattern", "") in q:
                    weight = float(kw.get("weight", 0.0))
                    score += weight
                    matched.append(Signal(id=kw.get("id", ""), weight=weight))

            for rx in rule.get("regex", []):
                pattern = rx.get("pattern", "")
                if pattern and re.search(pattern, q, flags=re.I):
                    weight = float(rx.get("weight", 0.0))
                    score += weight
                    matched.append(Signal(id=rx.get("id", ""), weight=weight))

            scored.append((cat, score, matched))

        if not scored:
            return {"category": "other", "confidence": 0.0, "signals": []}

        scored.sort(key=lambda x: x[1], reverse=True)
        top_cat, s1, m1 = scored[0]
        s2 = scored[1][1] if len(scored) > 1 else 0.0

        conf = 0.0 if s1 <= 0 else (s1 - s2) / (s1 + 1e-6)
        conf = max(0.0, min(1.0, conf))

        min_score = float(self.thresholds.get("min_score", 0.0))
        min_confidence = float(self.thresholds.get("min_confidence", 0.0))
        category = top_cat
        if s1 < min_score or conf < min_confidence:
            category = "other"

        return {
            "category": category,
            "confidence": conf,
            "signals": [s.dict() for s in m1],
        }
