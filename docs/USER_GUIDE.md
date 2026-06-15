# Code Puppy CN 用户手册

本文面向使用 Code Puppy CN 完成日常开发任务的个人开发者和企业用户。
管理员部署企业平台时，请同时阅读企业平台仓库中的管理员手册。

## 1. 产品能做什么

Code Puppy CN 是运行在终端中的 AI 编程助手，可以：

- 阅读和搜索项目代码；
- 创建、修改和删除文件；
- 执行 Shell 命令、构建和测试；
- 分析失败原因并完成代码修复闭环；
- 使用 Agent、Skills 和 MCP 扩展工作流；
- 在简体中文和英文之间即时切换；
- 连接个人模型服务，或接入企业统一管理的模型网关。

建议始终在 Git 仓库中使用，并在任务前确认工作区状态：

```bash
git status
```

## 2. 安装

### 2.1 环境要求

- Python 3.11 至 3.14
- Git
- [uv](https://docs.astral.sh/uv/)
- macOS、Linux 或 Windows

安装 `uv`：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2.2 从 GitHub 安装

```bash
git clone https://github.com/clawbobot/code-puppy-cn.git
cd code-puppy-cn
uv tool install --force .
```

如果出现命令不在 `PATH` 的提示：

```bash
uv tool update-shell
```

也可以在当前终端临时执行：

```bash
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

验证安装：

```bash
pup-cn --version
pup-cn-doctor --json --no-network
```

### 2.3 升级与卸载

在本地仓库更新后重新安装：

```bash
git pull
uv tool install --force .
```

卸载：

```bash
uv tool uninstall code-puppy-cn
```

## 3. 第一次启动

进入需要处理的项目目录后启动：

```bash
cd /path/to/your-project
pup-cn
```

首次启动会根据系统语言推荐中文或英文。切换语言：

```text
/language zh-CN
/language en-US
```

中文别名：

```text
/语言
```

语言选择会保存在本地配置中，重启后继续生效。切换只影响后续消息，
不会重新翻译已经显示的历史内容。

## 4. 配置个人模型

### 4.1 交互式配置

在 Code Puppy CN 中执行：

```text
/cn-setup
```

向导会从 models.dev 注册表读取模型信息，并展示常用的中国区服务商：

- 阿里云百炼；
- DeepSeek；
- Moonshot AI；
- Z.AI。

依次选择服务商、模型并输入凭证。模型名称以注册表中的官方名称为准。

查看候选模型：

```text
/cn-setup list
```

非交互添加方式：

```text
/cn-setup <provider-id> <model-id>
```

例如先通过 `list` 获得准确 ID，再执行添加，避免手工猜测模型名称。

### 4.2 模型切换

```text
/model
```

使用菜单查看已配置模型并切换当前模型。模型要完成代码修改任务，通常需要支持
Tool Calling；可以通过诊断工具确认。

### 4.3 Gemini 与 Vertex AI

Google 模型需要额外依赖：

```bash
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

Vertex AI 还需要配置 Google Cloud 项目、区域和 Application Default
Credentials。不要把 OAuth 授权码、服务账号密钥或 API Key 写入仓库。

## 5. 完成第一个代码任务

推荐按以下方式描述任务：

```text
先阅读项目和相关测试，运行测试复现问题。只修改必要文件，修复后再次运行测试，
最后总结根因、修改文件和测试结果。
```

一个可靠任务应包含四个阶段：

1. 理解项目和约束；
2. 运行测试，确认问题确实存在；
3. 修改最少的必要代码；
4. 再次运行测试并报告结果。

在任务结束后检查：

```bash
git diff --check
git diff
git status
```

不要仅根据模型的文字总结判断成功，应以真实测试、构建或静态检查结果为准。

## 6. 常用交互命令

| 命令 | 用途 |
| --- | --- |
| `/help` | 查看当前版本全部命令及本地化说明 |
| `/model` | 查看和切换模型 |
| `/agents` | 查看和切换 Agent |
| `/skills` | 查看可用 Skills |
| `/mcp` | 管理 MCP 服务 |
| `/session` | 管理会话 |
| `/diff` | 配置代码差异显示 |
| `/language` | 查看或切换界面语言 |
| `/cn-setup` | 配置常用模型 |
| `/doctor-cn` | 诊断本地模型环境 |
| `/enterprise` | 查看企业连接状态 |
| `/policy` | 查看企业下发策略 |
| `/usage` | 查看当前用户可见用量 |
| `/audit-status` | 查看心跳和审计上报状态 |

具体命令以安装版本中的 `/help` 为准。

## 7. 诊断

### 7.1 交互诊断

```text
/doctor-cn
/doctor-cn --live
```

`--live` 会发起最小真实调用，可能产生少量 Token 和费用。

### 7.2 命令行诊断

```bash
pup-cn-doctor
pup-cn-doctor --json
pup-cn-doctor --json --no-network
pup-cn-doctor --live
pup-cn-doctor --model <model-id> --timeout 15
```

JSON 字段固定使用英文，便于 CI 和脚本处理。凭证会被脱敏，但分享报告前仍应
人工检查内部域名、项目路径和其他业务信息。

## 8. 使用 code-fix Skill

仓库提供一个确定性的演示项目：

```bash
cd demo/code-fix
python -m pytest -q
pup-cn
```

输入：

```text
使用 code-fix skill 修复当前项目。先运行 `python -m pytest -q`，
只修改必要文件，修复后重新运行测试并总结结果。
```

验收标准：

- 初始测试失败；
- Agent 修改业务文件而不是测试；
- 最终测试通过；
- 输出包含修改和验证结果。

维护者可运行隔离的重复验收：

```bash
uv run python scripts/live_acceptance.py \
  --model <model-id> \
  --locale zh-CN \
  --runs 3 \
  --min-success-rate 0.8 \
  --output live-acceptance.json
```

真实模型存在随机性。超时或工具循环应视为失败并调查，不应只检查最终文件是否
碰巧可用。

## 9. 企业模式

企业模式由管理员提供平台地址。登录：

```bash
pup-cn enterprise login --server https://enterprise-ai.example.com
```

终端会显示授权页面和设备码。浏览器完成批准后，客户端会：

1. 获取设备访问令牌；
2. 下载并校验 Ed25519 签名配置；
3. 保存平台允许的模型、项目和策略；
4. 自动发送设备心跳。

查看状态：

```bash
pup-cn enterprise status
```

同步最新配置：

```bash
pup-cn enterprise sync
```

退出并删除本地企业凭证：

```bash
pup-cn enterprise logout
```

交互模式还支持：

```text
/enterprise
/enterprise sync
/policy
/usage
/audit-status
```

企业模式启用后，只允许选择平台下发的模型。配置过期、签名变化或验签失败时，
客户端默认拒绝继续使用企业模型。签名公钥变化需要管理员确认并重新注册设备。

## 10. 数据与安全

- 不要把 `.env`、API Key、OAuth 令牌、云凭证或企业状态目录提交到 Git。
- 运行任务前确认当前目录，避免 Agent 处理错误的项目。
- 对删除、发布、数据库迁移和基础设施命令保持人工确认。
- 企业审计默认只上报工具名、耗时、结果、项目路径哈希等元数据，不应上传完整
  源码或完整提示词。
- 如果密钥曾出现在聊天、终端历史或提交记录中，应立即轮换。

## 11. 常见问题

### `pup-cn: command not found`

```bash
uv tool update-shell
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

然后重新打开终端并运行 `pup-cn --version`。

### Google 插件提示缺少 `google-genai`

如果不使用 Google 模型，该警告不影响其他模型。需要 Google 模型时安装：

```bash
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

### Agent 找不到 `pytest`

优先使用当前 Python 环境运行：

```text
请运行 `python -m pytest -q`，不要直接运行 `pytest`。
```

并确认启动 `pup-cn` 的终端已经激活项目虚拟环境。

### 企业登录一直等待

- 确认平台 `/health` 可访问；
- 确认浏览器已批准正确的设备码；
- 检查设备码是否过期；
- 本地试点可由管理员检查 `/device` 页面和 Keycloak 登录状态。

### 企业配置过期

```bash
pup-cn enterprise sync
```

如果仍失败，检查平台时间、签名密钥是否改变，以及访问令牌是否已失效。

### 模型反复调用工具但不结束

中止任务，检查模型 Tool Calling 兼容性，并把测试命令、允许修改范围和完成条件
写得更明确。小模型应优先使用短任务和确定性的验收条件。

## 12. 获取帮助

提交问题前请提供：

- `pup-cn --version`；
- 操作系统和 Python 版本；
- 已脱敏的 `pup-cn-doctor --json`；
- 可复现步骤和期望结果；
- 不包含密钥、源码和内部地址的错误片段。

项目地址：<https://github.com/clawbobot/code-puppy-cn>
## 13. 企业试点命令

登录并同步签名配置后，可以运行：

```bash
pup-cn enterprise status
pup-cn enterprise doctor
```

`doctor` 会检查本地配置有效期、平台就绪状态、企业网关和可用模型。企业任务默认
限制为最多 12 次模型请求、20 次工具调用、100,000 Token 和 600 秒；平台可以
通过签名配置调整这些值。达到限制后返回 `task_limit_exceeded`。
