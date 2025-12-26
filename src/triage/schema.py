import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Signal:
    id: str
    weight: float

    def dict(self):
        return asdict(self)


@dataclass
class TriageResult:
    category: str
    confidence: float
    signals: List[Signal]

    def dict(self):
        formatted = []
        for s in self.signals:
            if hasattr(s, "dict"):
                formatted.append(s.dict())
            elif isinstance(s, dict):
                formatted.append(s)
        return {"category": self.category, "confidence": self.confidence, "signals": formatted}


@dataclass
class Citation:
    case_id: str
    source: str
    topic_url: str
    title: Optional[str] = ""
    forum: Optional[str] = ""
    snippet: str = ""
    score: float = 0.0

    def dict(self):
        return asdict(self)


@dataclass
class ActionPlan:
    next_questions: List[str]
    diagnostic_steps: List[str]

    def dict(self):
        return asdict(self)


@dataclass
class Query:
    text: str

    def dict(self):
        return asdict(self)


@dataclass
class Meta:
    generated_at: datetime
    rules_version: str
    index_version: str

    def dict(self):
        return {
            "generated_at": self.generated_at.isoformat(),
            "rules_version": self.rules_version,
            "index_version": self.index_version,
        }


@dataclass
class PipelineOutput:
    query: Query
    triage: TriageResult
    citations: List[Citation]
    action_plan: ActionPlan
    meta: Meta
    schema_version: str = field(default="0.1", init=False)

    def dict(self):
        return {
            "schema_version": self.schema_version,
            "query": self.query.dict(),
            "triage": self.triage.dict(),
            "citations": [c.dict() for c in self.citations],
            "action_plan": self.action_plan.dict(),
            "meta": self.meta.dict(),
        }

    def json(self):
        return json.dumps(self.dict(), ensure_ascii=False, default=str)

    @classmethod
    def parse_obj(cls, obj):
        inst = cls(
            query=Query(**obj.get("query", {})),
            triage=TriageResult(
                category=obj.get("triage", {}).get("category"),
                confidence=obj.get("triage", {}).get("confidence", 0.0),
                signals=[Signal(**s) for s in obj.get("triage", {}).get("signals", [])],
            ),
            citations=[Citation(**c) for c in obj.get("citations", [])],
            action_plan=ActionPlan(**obj.get("action_plan", {})),
            meta=Meta(
                generated_at=datetime.fromisoformat(obj.get("meta", {}).get("generated_at")),
                rules_version=obj.get("meta", {}).get("rules_version", ""),
                index_version=obj.get("meta", {}).get("index_version", ""),
            ),
        )
        inst.schema_version = obj.get("schema_version", inst.schema_version)
        return inst
