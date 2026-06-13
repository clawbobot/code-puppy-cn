"""Run isolated, repeatable Code Puppy CN coding-loop acceptance tests."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _prompt(locale: str) -> str:
    if locale == "zh-CN":
        return (
            "使用 code-fix skill 修复当前项目。先运行测试复现问题，只修改必要文件，"
            "修复后再次运行测试，并用中文总结修改和测试结果。"
        )
    return (
        "Use the code-fix skill to repair this project. Reproduce the failing tests, "
        "change only required files, rerun tests, and summarize changes and results "
        "in English."
    )


def run_once(
    source: Path,
    model: str,
    locale: str,
    timeout: int,
    index: int,
) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="code-puppy-cn-live-") as temp_dir:
        project = Path(temp_dir) / "code-fix"
        shutil.copytree(source, project)
        command = [
            sys.executable,
            "-m",
            "code_puppy",
            "--model",
            model,
            "--prompt",
            _prompt(locale),
        ]
        try:
            agent = subprocess.run(
                command,
                cwd=project,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            tests = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            success = agent.returncode == 0 and tests.returncode == 0
            return {
                "run": index,
                "success": success,
                "duration_seconds": round(time.perf_counter() - started, 2),
                "agent_exit_code": agent.returncode,
                "test_exit_code": tests.returncode,
                "test_output": tests.stdout[-500:],
                "agent_output_tail": (agent.stdout + agent.stderr)[-1500:],
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "run": index,
                "success": False,
                "duration_seconds": round(time.perf_counter() - started, 2),
                "error": f"timeout after {exc.timeout} seconds",
            }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", required=True, help="Configured Code Puppy model key"
    )
    parser.add_argument("--locale", choices=("zh-CN", "en-US"), default="zh-CN")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = Path(__file__).parents[1] / "demo" / "code-fix"
    results = [
        run_once(source, args.model, args.locale, args.timeout, index)
        for index in range(1, args.runs + 1)
    ]
    passed = sum(item["success"] for item in results)
    report = {
        "schema_version": 1,
        "model": args.model,
        "locale": args.locale,
        "passed": passed,
        "total": len(results),
        "success_rate": passed / len(results) if results else 0,
        "results": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["success_rate"] >= 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
