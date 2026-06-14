"""Install a built wheel in isolation and verify the public executables."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test a Code Puppy CN wheel in a clean virtual environment"
    )
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()

    wheel = args.wheel.resolve()
    if not wheel.is_file():
        parser.error(f"wheel not found: {wheel}")

    uv = shutil.which("uv")
    if uv is None:
        parser.error("uv is required")

    with tempfile.TemporaryDirectory(prefix="code-puppy-cn-smoke-") as temp_dir:
        root = Path(temp_dir)
        environment = root / ".venv"
        _run([uv, "venv", str(environment), "--python", "3.13"], cwd=root)

        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        _run([uv, "pip", "install", "--python", str(python), str(wheel)], cwd=root)

        metadata_version = _run(
            [
                str(python),
                "-c",
                (
                    "from importlib.metadata import version; "
                    "print(version('code-puppy-cn'))"
                ),
            ],
            cwd=root,
        ).stdout.strip()
        version = _run([str(scripts / "pup-cn"), "--version"], cwd=root)
        if version.stdout.strip() != metadata_version:
            raise RuntimeError(
                "CLI and package versions differ: "
                f"{version.stdout.strip()!r} != {metadata_version!r}"
            )

        doctor = _run(
            [str(scripts / "pup-cn-doctor"), "--json", "--no-network"],
            cwd=root,
        )
        report = json.loads(doctor.stdout)
        if report.get("schema_version") != 1:
            raise RuntimeError("diagnostic JSON schema_version is missing or invalid")

        resources = _run(
            [
                str(python),
                "-c",
                (
                    "from code_puppy.i18n import available_locales; "
                    "assert set(available_locales()) == {'en-US', 'zh-CN'}"
                ),
            ],
            cwd=root,
        )
        if resources.stderr:
            print(resources.stderr, file=sys.stderr, end="")

    print(f"Smoke test passed: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
