from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import json

from .action_plan import ActionPlanner
from .retriever_tfidf import TfidfRetriever
from .rule_classifier import RuleClassifier
from .schema import PipelineOutput, Query, TriageResult, Citation, ActionPlan, Meta, Signal


@dataclass
class PipelineVersions:
    rules_version: str
    index_version: str


def now_iso8601() -> datetime:
    return datetime.now(timezone.utc)


def load_yaml(path: Path) -> Dict:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        fallback = path.with_suffix(".json")
        if fallback.exists():
            with fallback.open("r", encoding="utf-8") as f:
                return json.load(f)
        raise


class Pipeline:
    def __init__(self, classifier: RuleClassifier, retriever: TfidfRetriever, planner: ActionPlanner, versions: PipelineVersions):
        self.classifier = classifier
        self.retriever = retriever
        self.planner = planner
        self.versions = versions

    def run(self, query_text: str) -> PipelineOutput:
        triage_raw = self.classifier.classify(query_text)
        citations_raw = self.retriever.search(query_text, top_k=5)
        action_plan_raw = self.planner.generate(triage_raw.get("category"), triage_raw.get("confidence", 0.0))

        signals = [Signal(**s) for s in triage_raw.get("signals", [])]
        triage = TriageResult(category=triage_raw.get("category"), confidence=triage_raw.get("confidence", 0.0), signals=signals)
        citations = [Citation(**c) for c in citations_raw]
        action_plan = ActionPlan(**action_plan_raw)
        meta = Meta(
            generated_at=now_iso8601(),
            rules_version=self.versions.rules_version,
            index_version=self.versions.index_version,
        )

        return PipelineOutput(
            query=Query(text=query_text),
            triage=triage,
            citations=citations,
            action_plan=action_plan,
            meta=meta,
        )


def load_default_pipeline(base_dir: Path = None) -> Pipeline:
    base_dir = base_dir or Path(__file__).resolve().parents[2]
    rules_cfg = load_yaml(base_dir / "configs" / "rules.yaml")
    playbooks_cfg = load_yaml(base_dir / "configs" / "playbooks.yaml")

    index_path = base_dir / "artifacts" / "tfidf.joblib"
    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found at {index_path}. Please run scripts/build_index.py first.")

    classifier = RuleClassifier(rules_cfg)
    retriever = TfidfRetriever(index_path)
    planner = ActionPlanner(playbooks_cfg)

    versions = PipelineVersions(
        rules_version=rules_cfg.get("version", ""),
        index_version=retriever.index_version,
    )
    return Pipeline(classifier, retriever, planner, versions)
