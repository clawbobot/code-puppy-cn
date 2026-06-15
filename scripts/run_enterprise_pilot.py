"""Run the fixed 4/3/3 single-user enterprise pilot matrix."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--locale", choices=("zh-CN", "en-US"), default="zh-CN")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matrix = (("python", 4), ("typescript", 3), ("build", 3))
    summaries = []
    exit_code = 0
    script = Path(__file__).with_name("live_acceptance.py")
    for project, runs in matrix:
        output = args.output_dir / f"{project}.json"
        command = [
            sys.executable,
            str(script),
            "--model",
            args.model,
            "--project",
            project,
            "--runs",
            str(runs),
            "--locale",
            args.locale,
            "--timeout",
            str(args.timeout),
            "--min-success-rate",
            "0",
            "--output",
            str(output),
            "--keep-projects",
            str(args.output_dir / "projects" / project),
        ]
        completed = subprocess.run(command, check=False)
        exit_code = max(exit_code, completed.returncode)
        summaries.append(json.loads(output.read_text(encoding="utf-8")))

    passed = sum(summary["passed"] for summary in summaries)
    total = sum(summary["total"] for summary in summaries)
    combined = {
        "schema_version": 1,
        "model": args.model,
        "locale": args.locale,
        "passed": passed,
        "total": total,
        "success_rate": passed / total if total else 0,
        "accepted": total == 10 and passed >= 8,
        "projects": summaries,
    }
    combined_path = args.output_dir / "pilot-summary.json"
    combined_path.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    return 0 if combined["accepted"] else max(exit_code, 1)


if __name__ == "__main__":
    raise SystemExit(main())
