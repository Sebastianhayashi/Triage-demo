import argparse
import json
from pathlib import Path

from triage.pipeline import load_default_pipeline


def main():
    parser = argparse.ArgumentParser(description="WPML support triage CLI")
    parser.add_argument("text", nargs="?", help="User query text")
    parser.add_argument("--base", type=Path, default=None, help="Base directory for configs and artifacts")
    args = parser.parse_args()

    if not args.text:
        parser.error("Please provide query text")

    pipeline = load_default_pipeline(args.base)
    output = pipeline.run(args.text)
    print(json.dumps(output.dict(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
