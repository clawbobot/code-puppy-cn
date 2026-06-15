import sys
import tomllib
from pathlib import Path


def test_project_supports_current_python():
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    requirement = config["project"]["requires-python"]
    assert requirement == f">={sys.version_info.major}.{sys.version_info.minor}"
