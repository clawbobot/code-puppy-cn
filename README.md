<div align="center">
  <img src="code_puppy.png" alt="Code Puppy CN" width="160">

  # Code Puppy CN

  **为中文开发者优化的双语终端 AI 编程助手**

  [English](README_EN.md) | 简体中文

  [![CI](https://github.com/clawbobot/code-puppy-cn/actions/workflows/ci.yml/badge.svg)](https://github.com/clawbobot/code-puppy-cn/actions/workflows/ci.yml)
  [![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

Code Puppy CN 是一个运行在终端中的 AI 编程助手。它能够理解项目、编辑文件、执行命令和测试，并为中国区常用模型提供更顺畅的配置、诊断与中文交互体验。

项目支持随时切换简体中文和英文，同时保留 Code Puppy 的 Agent、Skills、MCP 与模型扩展能力。

完整安装、配置、任务实践、企业接入与故障排查请阅读
[中文用户手册](docs/USER_GUIDE.md)；英文用户请阅读
[English User Guide](docs/USER_GUIDE_EN.md)。

## 核心能力

- **自然语言编程**：分析代码、定位问题、实现功能、重构并补充测试。
- **完整任务闭环**：读取项目、修改文件、运行 Shell 命令和测试、总结结果。
- **双语界面**：首次启动自动检测系统语言，运行中可立即切换中文或英文。
- **模型快速配置**：引导配置通义、DeepSeek、Kimi 和 GLM 等中国区常用模型。
- **环境诊断**：检查运行环境、网络、凭证、Endpoint 与模型工具调用能力。
- **可扩展工作流**：兼容 Code Puppy 的 Agent、Skill、MCP 和插件机制。
- **跨平台运行**：支持 macOS、Linux 和 Windows。

## 环境要求

- Python 3.11 至 3.14
- Git
- [uv](https://docs.astral.sh/uv/)
- 至少一个模型服务商的 API Key

## 安装

### 1. 安装 uv

macOS 或 Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装 Code Puppy CN

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv tool install --force .
```

如果终端提示命令不在 `PATH` 中，请执行：

```bash
uv tool update-shell
```

重新打开终端后验证安装：

```bash
pup-cn --version
```

## 快速开始

启动 Code Puppy CN：

```bash
pup-cn
```

首次启动时，程序会根据系统语言推荐中文或英文。进入主界面后，运行：

```text
/cn-setup
```

根据向导选择服务商和模型，输入对应的 API Key。配置完成后，即可直接描述开发任务，例如：

```text
分析这个项目，修复当前失败的测试，并说明修改原因。
```

任务完成后可以运行诊断：

```text
/doctor-cn
```

## 支持的模型服务

配置向导会从模型注册表获取最新可用模型，并优先展示支持工具调用、适合编码任务的选项。

| 服务商 | 常见模型系列 | 配置入口 |
| --- | --- | --- |
| 阿里云百炼 | Qwen / 通义千问 | `/cn-setup` |
| DeepSeek | DeepSeek Chat / Reasoner | `/cn-setup` |
| Moonshot AI | Kimi | `/cn-setup` |
| 智谱 Z.AI | GLM | `/cn-setup` |

实际可选模型以配置向导显示的最新列表为准。

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `/help` | 查看所有可用命令 |
| `/cn-setup` | 交互式配置中国区常用模型 |
| `/cn-setup list` | 查看支持的服务商与推荐模型 |
| `/language` | 查看当前语言和切换方式 |
| `/language zh-CN` | 切换为简体中文 |
| `/language en-US` | 切换为英文 |
| `/语言` | 查看当前语言和切换方式 |
| `/doctor-cn` | 检查本地环境和模型配置 |
| `/doctor-cn --live` | 通过最小真实请求验证模型连接 |
| `/model` | 查看或切换当前模型 |
| `/agents` | 查看和切换 Agent |
| `/skills` | 查看可用 Skills |
| `/mcp` | 管理 MCP 服务 |
| `/diff` | 配置代码差异的高亮颜色 |
| `/session` | 管理会话 |

在交互界面中运行 `/help`，可以查看当前版本提供的完整命令列表。

## 企业模式

连接 Code Puppy Enterprise 后，客户端会通过设备授权登录，校验平台签名的配置，并仅使用平台批准的模型网关。模型 Endpoint、凭证、策略、预算和审计规则由企业平台统一下发。

```bash
pup-cn enterprise login --server https://ai-gateway.example.com
pup-cn enterprise status
pup-cn enterprise sync
pup-cn enterprise logout
```

交互界面还提供：

| 命令 | 说明 |
| --- | --- |
| `/enterprise` | 查看企业连接和配置状态 |
| `/enterprise sync` | 立即同步签名配置 |
| `/policy` | 查看当前企业策略 |
| `/usage` | 查看个人可见的模型用量 |
| `/audit-status` | 查看审计连接状态 |

企业配置过期或验签失败时，客户端默认停止企业模型任务，避免绕过平台网关。

## 诊断工具

除了交互命令，也可以直接在终端运行诊断：

```bash
pup-cn-doctor
```

输出适合自动化处理的 JSON：

```bash
pup-cn-doctor --json
```

执行最小真实模型调用：

```bash
pup-cn-doctor --live
```

其他常用参数：

```bash
pup-cn-doctor --no-network
pup-cn-doctor --model <model-id>
pup-cn-doctor --timeout 15
```

诊断报告会对敏感信息进行脱敏，但仍建议在分享前检查输出内容。

## 使用示例

Code Puppy CN 适合处理从代码理解到验证交付的完整任务：

```text
阅读当前项目并解释主要模块。
```

```text
为用户登录接口增加参数校验，并补充单元测试。
```

```text
找出测试失败的原因，修复问题并重新运行测试。
```

```text
检查当前 Git diff，指出可能的回归风险。
```

执行文件修改、Shell 命令或其他敏感操作前，程序会根据当前权限设置请求确认。

## Google Gemini 与 Vertex AI

如需使用 Google Gemini 或 Vertex AI，请安装 Google 可选依赖：

```bash
cd code-puppy-cn
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

之后可通过现有模型配置流程添加并选择 Google 模型。Vertex AI 还需要在本地配置有效的 Google Cloud 项目、区域和应用默认凭证。

## 配置与安全

- API Key 和本地偏好设置保存在用户配置目录中。
- 不要把 API Key、云凭证或包含敏感信息的配置文件提交到 Git。
- 建议使用环境变量或交互式配置向导录入凭证。
- 公开分享日志和诊断报告前，请再次确认其中不包含业务代码或内部地址。
- 如果密钥曾出现在聊天、终端历史或公开仓库中，请立即前往对应服务商控制台轮换。

## 从源码开发

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv sync --all-groups
uv run pytest
```

运行本地版本：

```bash
uv run pup-cn
```

构建发行包：

```bash
uv build
```

## 项目关系

Code Puppy CN 基于开源项目 [Code Puppy](https://github.com/mpfaffenberger/code_puppy) 构建，并持续跟进上游能力。这个发行版重点改善中文界面、中国区模型配置、连接诊断和本地使用体验。

感谢 Code Puppy 作者及所有开源贡献者。

## 参与贡献

欢迎通过 [Issues](https://github.com/clawbobot/code-puppy-cn/issues) 报告问题、提出功能建议或提交改进。

提交代码前，请确保：

```bash
uv run pytest
uv build
```

## 许可证

本项目采用 [MIT License](LICENSE)，并保留原项目的版权与作者信息。
