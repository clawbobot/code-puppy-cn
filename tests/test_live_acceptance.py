from scripts.live_acceptance import meets_success_threshold, snapshot_source_files


def test_snapshot_source_files_ignores_test_caches(tmp_path):
    (tmp_path / "calculator.py").write_text("value = 1\n", encoding="utf-8")
    cache = tmp_path / ".pytest_cache"
    cache.mkdir()
    (cache / "state").write_text("changed", encoding="utf-8")
    bytecode = tmp_path / "__pycache__"
    bytecode.mkdir()
    (bytecode / "calculator.pyc").write_bytes(b"compiled")

    assert snapshot_source_files(tmp_path) == {"calculator.py": "value = 1\n"}


def test_success_threshold_supports_two_of_three():
    assert meets_success_threshold(2, 3, 2 / 3)
    assert not meets_success_threshold(1, 3, 2 / 3)
    assert not meets_success_threshold(0, 0, 0)
