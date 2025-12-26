import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "src"))

from scripts.build_index import build_index
from triage.pipeline import load_default_pipeline
from triage.schema import PipelineOutput


def ensure_index():
    index_path = BASE_DIR / "artifacts" / "tfidf.joblib"
    if not index_path.exists():
        cases_path = BASE_DIR / "data" / "cases.cleaned.jsonl"
        build_index(cases_path, index_path)
    return index_path


def test_pipeline_smoke():
    ensure_index()
    pipeline = load_default_pipeline(BASE_DIR)
    query = "Translation editor does not open for WooCommerce products"
    output = pipeline.run(query)

    # validate schema
    parsed = PipelineOutput.parse_obj(json.loads(output.json()))

    assert parsed.action_plan.next_questions, "next_questions should not be empty"
    assert parsed.action_plan.diagnostic_steps, "diagnostic_steps should not be empty"
    assert parsed.citations, "citations should not be empty"
    assert parsed.meta.rules_version, "rules_version should be set"
    assert parsed.meta.index_version, "index_version should be set"
