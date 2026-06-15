"""Run isolated, repeatable Code Puppy CN coding-loop acceptance tests."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def snapshot_source_files(project: Path) -> dict[str, str]:
    ignored_parts = {"__pycache__", ".pytest_cache"}
    return {
        path.relative_to(project).as_posix(): path.read_text(encoding="utf-8")
        for path in project.rglob("*")
        if path.is_file()
        and not ignored_parts.intersection(path.parts)
        and path.suffix != ".pyc"
    }


def meets_success_threshold(passed: int, total: int, minimum: float) -> bool:
    return total > 0 and passed / total >= minimum


def _prompt(locale: str) -> str:
    if locale == "zh-CN":
        return (
            "使用 code-fix skill 修复当前项目。先运行 `python -m pytest -q` 复现问题，"
            "只修改必要文件，修复后再次运行同一测试命令，并用中文总结修改和测试结果。"
        )
    return (
        "Use the code-fix skill to repair this project. Run `python -m pytest -q` "
        "to reproduce the failure, change only required files, rerun the same test "
        "command, and summarize changes and results in English."
    )


def run_once(
    source: Path,
    model: str,
    locale: str,
    timeout: int,
    index: int,
    keep_projects: Path | None = None,
) -> dict:
    started = time.perf_counter()
    if keep_projects:
        temp_dir = keep_projects / f"run-{index}"
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True)
        cleanup = None
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="code-puppy-cn-live-")
        temp_dir = Path(cleanup.name)
    try:
        project = Path(temp_dir) / "code-fix"
        shutil.copytree(source, project, ignore=shutil.ignore_patterns("__pycache__"))
        baseline = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        before = snapshot_source_files(project)
        command = [
            sys.executable,
            "-m",
            "code_puppy",
            "--agent",
            "code-puppy",
            "--model",
            model,
            "--prompt",
            _prompt(locale),
        ]
        try:
            agent_env = os.environ.copy()
            agent_env["PATH"] = (
                f"{Path(sys.executable).parent}{os.pathsep}"
                f"{agent_env.get('PATH', '')}"
            )
            agent = subprocess.run(
                command,
                cwd=project,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                env=agent_env,
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
            after = snapshot_source_files(project)
            changed_files = sorted(
                path
                for path in before.keys() | after.keys()
                if before.get(path) != after.get(path)
            )
            allowed_changes = {"calculator.py"}
            success = (
                baseline.returncode != 0
                and agent.returncode == 0
                and tests.returncode == 0
                and bool(changed_files)
                and set(changed_files) <= allowed_changes
            )
            return {
                "run": index,
                "success": success,
                "duration_seconds": round(time.perf_counter() - started, 2),
                "baseline_test_exit_code": baseline.returncode,
                "agent_exit_code": agent.returncode,
                "test_exit_code": tests.returncode,
                "changed_files": changed_files,
                "baseline_output": baseline.stdout[-500:],
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
    finally:
        if cleanup:
            cleanup.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", required=True, help="Configured Code Puppy model key"
    )
    parser.add_argument("--locale", choices=("zh-CN", "en-US"), default="zh-CN")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--min-success-rate",
        type=float,
        default=0.8,
        help="Required success rate from 0.0 to 1.0 (default: 0.8).",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--keep-projects",
        type=Path,
        help="Keep each isolated run directory for manual inspection.",
    )
    args = parser.parse_args()
    if not 0 <= args.min_success_rate <= 1:
        parser.error("--min-success-rate must be between 0.0 and 1.0")

    source = Path(__file__).parents[1] / "demo" / "code-fix"
    results = [
        run_once(
            source,
            args.model,
            args.locale,
            args.timeout,
            index,
            args.keep_projects,
        )
        for index in range(1, args.runs + 1)
    ]
    passed = sum(item["success"] for item in results)
    report = {
        "schema_version": 1,
        "model": args.model,
        "locale": args.locale,
        "enterprise_mode": bool(os.environ.get("CODE_PUPPY_ENTERPRISE_HOME")),
        "passed": passed,
        "total": len(results),
        "success_rate": passed / len(results) if results else 0,
        "required_success_rate": args.min_success_rate,
        "results": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return (
        0
        if meets_success_threshold(passed, len(results), args.min_success_rate)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
