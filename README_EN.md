<div align="center">
  <img src="code_puppy.png" alt="Code Puppy CN" width="160">

  # Code Puppy CN

  **A bilingual terminal coding agent optimized for developers in China**

  English | [简体中文](README.md)

  [![CI](https://github.com/clawbobot/code-puppy-cn/actions/workflows/ci.yml/badge.svg)](https://github.com/clawbobot/code-puppy-cn/actions/workflows/ci.yml)
  [![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

Code Puppy CN is an AI coding agent that runs in your terminal. It can understand a project, edit files, execute commands and tests, and provide a streamlined setup and diagnostic experience for AI model services commonly used in China.

The interface can switch between Simplified Chinese and English at any time while retaining Code Puppy's Agent, Skills, MCP, and model extension capabilities.

For complete installation, configuration, workflow, enterprise enrollment, and
troubleshooting instructions, see the
[English User Guide](docs/USER_GUIDE_EN.md) or
[中文用户手册](docs/USER_GUIDE.md).

## Highlights

- **Natural-language coding**: analyze code, locate defects, implement features, refactor, and add tests.
- **End-to-end execution**: inspect a project, edit files, run shell commands and tests, and summarize the result.
- **Bilingual interface**: detect the system language on first launch and switch languages immediately.
- **Guided model setup**: configure Qwen, DeepSeek, Kimi, GLM, and other supported models.
- **Built-in diagnostics**: inspect the runtime, network, credentials, endpoints, and model tool-calling support.
- **Extensible workflows**: use Code Puppy Agents, Skills, MCP servers, and plugins.
- **Cross-platform support**: run on macOS, Linux, and Windows.

## Requirements

- Python 3.11 through 3.14
- Git
- [uv](https://docs.astral.sh/uv/)
- An API key from at least one model provider

## Installation

### 1. Install uv

macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Code Puppy CN

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv tool install --force .
```

If the executable is not on your `PATH`, run:

```bash
uv tool update-shell
```

Open a new terminal and verify the installation:

```bash
pup-cn --version
```

## Quick Start

Launch Code Puppy CN:

```bash
pup-cn
```

On first launch, the application recommends Chinese or English based on your system language. In the main interface, run:

```text
/cn-setup
```

Choose a provider and model, then enter the corresponding API key. Once setup is complete, describe a development task directly:

```text
Analyze this project, fix the currently failing tests, and explain the changes.
```

After the task, verify your configuration with:

```text
/doctor-cn
```

## Supported Model Services

The setup wizard retrieves the latest model catalog and prioritizes options that support tool calling and coding workflows.

| Provider | Common model families | Setup |
| --- | --- | --- |
| Alibaba Cloud Model Studio | Qwen | `/cn-setup` |
| DeepSeek | DeepSeek Chat / Reasoner | `/cn-setup` |
| Moonshot AI | Kimi | `/cn-setup` |
| Z.AI | GLM | `/cn-setup` |

The models shown by the setup wizard are the source of truth for current availability.

## Common Commands

| Command | Description |
| --- | --- |
| `/help` | Show all available commands |
| `/cn-setup` | Configure commonly used model services interactively |
| `/cn-setup list` | List supported providers and recommended models |
| `/language` | Show the current language and switching options |
| `/language zh-CN` | Switch to Simplified Chinese |
| `/language en-US` | Switch to English |
| `/语言` | Show the current language and switching options |
| `/doctor-cn` | Check the local environment and model configuration |
| `/doctor-cn --live` | Verify model connectivity with a minimal live request |
| `/model` | View or switch the active model |
| `/agents` | View and switch Agents |
| `/skills` | Browse available Skills |
| `/mcp` | Manage MCP servers |
| `/diff` | Configure code-diff highlight colors |
| `/session` | Manage sessions |

Run `/help` in the interactive interface for the complete command list included in your installed version.

## Enterprise Mode

When connected to Code Puppy Enterprise, the client uses device authorization,
verifies platform-signed configuration, and routes work only through approved
enterprise models. Endpoints, credentials, policies, budgets, and audit rules
are managed by the platform.

```bash
pup-cn enterprise login --server https://ai-gateway.example.com
pup-cn enterprise status
pup-cn enterprise sync
pup-cn enterprise logout
```

Interactive commands:

| Command | Description |
| --- | --- |
| `/enterprise` | View enterprise connection and configuration status |
| `/enterprise sync` | Synchronize signed configuration immediately |
| `/policy` | View the active enterprise policy |
| `/usage` | View model usage visible to the current user |
| `/audit-status` | View the audit connection status |

The client fails closed when enterprise configuration expires or signature
verification fails, preventing a local model from bypassing the gateway.

## Diagnostics

Run diagnostics directly from your terminal:

```bash
pup-cn-doctor
```

Produce machine-readable JSON:

```bash
pup-cn-doctor --json
```

Perform a minimal live model request:

```bash
pup-cn-doctor --live
```

Other useful options:

```bash
pup-cn-doctor --no-network
pup-cn-doctor --model <model-id>
pup-cn-doctor --timeout 15
```

Diagnostic reports redact sensitive values, but you should still review the output before sharing it.

## Example Tasks

Code Puppy CN can handle a complete workflow from code discovery to verification:

```text
Read this project and explain its main modules.
```

```text
Add input validation to the login endpoint and include unit tests.
```

```text
Find the cause of the failing tests, fix it, and run the tests again.
```

```text
Review the current Git diff and identify potential regression risks.
```

Before editing files, running shell commands, or performing other sensitive operations, the application asks for confirmation according to the active permission settings.

## Google Gemini and Vertex AI

To use Google Gemini or Vertex AI, install the Google optional dependency:

```bash
cd code-puppy-cn
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

You can then add and select Google models through the existing model configuration flow. Vertex AI also requires a valid Google Cloud project, region, and Application Default Credentials on the local machine.

## Configuration and Security

- API keys and local preferences are stored in the user configuration directory.
- Never commit API keys, cloud credentials, or configuration files containing secrets.
- Prefer environment variables or the interactive setup wizard for credentials.
- Review logs and diagnostic reports before sharing them, especially when working with private source code or internal endpoints.
- Rotate any credential immediately if it has appeared in chat, terminal history, or a public repository.

## Development

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv sync --all-groups
uv run pytest
```

Run the local version:

```bash
uv run pup-cn
```

Build the distribution packages:

```bash
uv build
```

## Upstream Project

Code Puppy CN is built on the open-source [Code Puppy](https://github.com/mpfaffenberger/code_puppy) project and continues to follow upstream development. This distribution focuses on the bilingual interface, model setup for users in China, connectivity diagnostics, and a smoother local experience.

We are grateful to the Code Puppy authors and all open-source contributors.

## Contributing

Use [GitHub Issues](https://github.com/clawbobot/code-puppy-cn/issues) to report bugs, suggest features, or discuss improvements.

Before submitting code, run:

```bash
uv run pytest
uv build
```

## License

This project is available under the [MIT License](LICENSE) and retains the original project's copyright and attribution notices.
