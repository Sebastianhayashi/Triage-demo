from typing import Dict, List


class ActionPlanner:
    def __init__(self, playbooks_cfg: Dict):
        self.playbooks_cfg = playbooks_cfg
        self.low_conf = playbooks_cfg.get("low_confidence_threshold", 0.0)
        self.default = playbooks_cfg.get("default", {"next_questions": [], "diagnostic_steps": []})
        self.by_category = playbooks_cfg.get("by_category", {})
        self.playbooks_version = playbooks_cfg.get("version", "")

    def generate(self, category: str, confidence: float) -> Dict[str, List[str]]:
        if confidence < self.low_conf:
            tpl = self.default
        else:
            tpl = self.by_category.get(category, self.default)
        return {
            "next_questions": tpl.get("next_questions", []),
            "diagnostic_steps": tpl.get("diagnostic_steps", []),
        }
