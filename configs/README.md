# configs/

Configuration drives classification, retrieval guidance, and action planning. All YAML files have JSON fallbacks for environments without PyYAML, and their `version` fields are surfaced in pipeline outputs for traceability.

- **taxonomy.yaml / taxonomy.json** — Defines the category IDs, names, and scope boundaries. The RuleClassifier implicitly aligns with these IDs when scoring signals.
- **rules.yaml / rules.json** — Lists keywords/regex signals, per-category weights, and thresholds used by `RuleClassifier` to compute category scores and confidences.
- **playbooks.yaml / playbooks.json** — Provides default and per-category next questions plus diagnostic steps. `ActionPlanner` selects templates based on the classifier output and confidence.

When updating configs, bump the `version` field so downstream `meta.rules_version` fields and reproducibility checks stay informative.
