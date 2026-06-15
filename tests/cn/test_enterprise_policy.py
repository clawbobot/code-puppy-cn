from code_puppy.enterprise_policy import evaluate_tool_policy


POLICY = {
    "shell": {"deny": ["rm -rf", "git push --force"]},
    "files": {"deny": [".env", "*.pem", "*.key"]},
    "network": {"default": "deny", "allow": ["https://gateway.example"]},
    "skills": {"allow": ["code-fix"]},
    "mcp": {"default": "deny"},
}


def test_blocks_dangerous_shell_and_repeated_failure():
    assert evaluate_tool_policy(
        POLICY, "run_shell_command", {"command": "rm -rf build"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY, "run_shell_command", {"command": "cat .env"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY, "run_shell_command", {"command": "curl https://example.com"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY,
        "run_shell_command",
        {"command": "curl https://gateway.example/health"},
    ) is None
    assert evaluate_tool_policy(
        POLICY,
        "run_shell_command",
        {"command": "pytest"},
        repeated_failure_count=2,
    )["code"] == "policy_denied"


def test_blocks_sensitive_paths_and_unapproved_network(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert evaluate_tool_policy(
        POLICY, "write_file", {"path": ".env/credentials"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY,
        "edit_file",
        {"payload": {"file_path": "private.key", "content": "secret"}},
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY, "write_file", {"path": "client.pem"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(
        POLICY, "fetch_url", {"url": "https://example.com/data"}
    )["code"] == "policy_denied"
    assert (
        evaluate_tool_policy(
            POLICY, "fetch_url", {"url": "https://gateway.example/v1/models"}
        )
        is None
    )


def test_blocks_unapproved_skills_and_mcp():
    assert evaluate_tool_policy(
        POLICY, "activate_skill", {"skill_name": "unknown"}
    )["code"] == "policy_denied"
    assert evaluate_tool_policy(POLICY, "mcp_call", {})["code"] == "policy_denied"
