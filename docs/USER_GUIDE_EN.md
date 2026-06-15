# Code Puppy CN User Guide

This guide covers installation, personal model setup, coding workflows,
diagnostics, and enterprise enrollment.

## Install

Requirements: Python 3.11-3.14, Git, `uv`, and macOS, Linux, or Windows.

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv tool install --force .
uv tool update-shell
pup-cn --version
```

If the command is unavailable in the current shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

Upgrade by pulling the repository and running `uv tool install --force .`
again. Uninstall with:

```bash
uv tool uninstall code-puppy-cn
```

## First Run

Start the agent from the project you want it to work on:

```bash
cd /path/to/project
pup-cn
```

Switch the interface language at any time:

```text
/language zh-CN
/language en-US
```

The selection is persisted. Existing messages are not retranslated.

## Configure a Personal Model

Run:

```text
/cn-setup
```

The wizard retrieves the current models.dev catalog and presents supported
Alibaba Cloud, DeepSeek, Moonshot AI, and Z.AI options. Use:

```text
/cn-setup list
/cn-setup <provider-id> <model-id>
/model
```

Use the exact provider and model identifiers shown by the catalog. Coding tasks
normally require a model with Tool Calling support.

Google Gemini and Vertex AI require the optional dependency:

```bash
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

Vertex AI also requires a Google Cloud project, region, and Application Default
Credentials.

## Recommended Coding Workflow

Give the agent explicit verification criteria:

```text
Read the relevant code and tests. Run `python -m pytest -q` to reproduce the
failure, change only the necessary files, rerun the same test command, and
summarize the root cause, changed files, and results.
```

A reliable task should:

1. inspect the project and constraints;
2. reproduce the issue;
3. make the smallest necessary change;
4. run real tests or builds before reporting completion.

Review the result yourself:

```bash
git diff --check
git diff
git status
```

## Main Commands

| Command | Purpose |
| --- | --- |
| `/help` | Show the complete localized command list |
| `/model` | View or switch the active model |
| `/agents` | View or switch Agents |
| `/skills` | Browse Skills |
| `/mcp` | Manage MCP servers |
| `/session` | Manage sessions |
| `/language` | View or change the interface language |
| `/cn-setup` | Configure supported model services |
| `/doctor-cn` | Diagnose the environment |
| `/enterprise` | View enterprise connection state |
| `/policy` | View the active enterprise policy |
| `/usage` | View usage visible to the current user |
| `/audit-status` | View heartbeat and audit delivery state |

The installed version's `/help` output is the source of truth.

## Diagnostics

```bash
pup-cn-doctor
pup-cn-doctor --json
pup-cn-doctor --json --no-network
pup-cn-doctor --live
pup-cn-doctor --model <model-id> --timeout 15
```

`--live` makes a small real request and may consume tokens. JSON field names
remain in English for automation. Review redacted reports before sharing them.

## Enterprise Enrollment

Your administrator supplies the platform URL:

```bash
pup-cn enterprise login --server https://enterprise-ai.example.com
```

Open the displayed verification page and approve the device code. The client
then verifies a signed configuration, activates approved models, and sends a
heartbeat.

```bash
pup-cn enterprise status
pup-cn enterprise sync
pup-cn enterprise logout
```

Interactive commands:

```text
/enterprise
/enterprise sync
/policy
/usage
/audit-status
```

Enterprise mode only permits platform-managed models. Expired or invalid
configuration fails closed. A changed signing key requires administrator
approval and device re-enrollment.

## Security

- Never commit API keys, OAuth tokens, cloud credentials, `.env` files, or
  enterprise client state.
- Confirm the working directory before starting an agent.
- Review destructive, publishing, database, and infrastructure commands.
- Treat tests and builds as the completion signal, not the assistant summary.
- Rotate any secret exposed in chat, terminal history, or Git.

## Troubleshooting

`pup-cn: command not found`: run `uv tool update-shell`, add
`$HOME/.local/bin` to `PATH`, and reopen the terminal.

Missing `google-genai`: ignore it when Google models are unused, or reinstall
with the Google optional dependency shown above.

The agent cannot find `pytest`: ask it to use `python -m pytest -q` and start
Code Puppy from the project's activated environment.

Enterprise configuration expired: run `pup-cn enterprise sync`. If it still
fails, check platform time, token validity, and signing-key changes.

Tool loop or timeout: cancel the task, verify Tool Calling compatibility, and
use a shorter prompt with explicit commands, allowed files, and completion
criteria.

Project: <https://github.com/clawbobot/code-puppy-cn>
