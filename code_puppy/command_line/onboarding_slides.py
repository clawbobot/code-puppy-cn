"""Slide content for the onboarding wizard.

🐶 Lean, mean, ADHD-friendly slides. 5 slides max!
"""

from typing import List, Tuple

# ============================================================================
# Slide Data Constants
# ============================================================================

# Model subscription options
MODEL_OPTIONS: List[Tuple[str, str, str]] = [
    ("chatgpt", "ChatGPT Plus/Pro/Max", "OAuth login - no API key needed"),
    ("claude", "Claude Code Pro/Max", "OAuth login - no API key needed"),
    ("api_keys", "API Keys", "OpenAI, Anthropic, Google, etc."),
    ("openrouter", "OpenRouter", "Single key for 100+ models"),
    ("skip", "Skip for now", "Configure later with /set or /add_model"),
]


# ============================================================================
# Navigation Footer (shown on ALL slides)
# ============================================================================


def get_nav_footer() -> str:
    """Navigation hints shown at bottom of every slide."""
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        return (
            "\n[dim]─────────────────────────────────────[/dim]\n"
            "[green]→/l[/green] 下一步  "
            "[green]←/h[/green] 返回  "
            "[green]↑↓/jk[/green] 选择  "
            "[green]Enter[/green] 确认  "
            "[yellow]ESC[/yellow] 跳过"
        )
    return (
        "\n[dim]─────────────────────────────────────[/dim]\n"
        "[green]→/l[/green] Next  "
        "[green]←/h[/green] Back  "
        "[green]↑↓/jk[/green] Options  "
        "[green]Enter[/green] Select  "
        "[yellow]ESC[/yellow] Skip"
    )


# ============================================================================
# Gradient Banner
# ============================================================================


def get_gradient_banner() -> str:
    """Generate the gradient CODE PUPPY banner."""
    try:
        import pyfiglet

        lines = pyfiglet.figlet_format("CODE PUPPY", font="ansi_shadow").split("\n")
        colors = ["bright_blue", "bright_cyan", "bright_green"]
        result = []
        for i, line in enumerate(lines):
            if line.strip():
                color = colors[min(i // 2, len(colors) - 1)]
                result.append(f"[{color}]{line}[/{color}]")
        return "\n".join(result)
    except ImportError:
        return "[bold bright_cyan]═══ CODE PUPPY 🐶 ═══[/bold bright_cyan]"


# ============================================================================
# Slide Content (5 slides total)
# ============================================================================


def slide_welcome() -> str:
    """Slide 1: Welcome - quick intro."""
    content = get_gradient_banner()
    content += "\n\n"
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        content += "[bold white]欢迎使用！[/bold white]\n\n"
        content += "[cyan]快速设置：[/cyan]\n"
        content += "  1. 选择模型供应商\n"
        content += "  2. 可选：配置 MCP 服务\n"
        content += "  3. 了解不同智能体的适用场景\n"
        content += "  4. 开始编码\n\n"
        content += "[dim]大约需要 1 分钟。[/dim]"
        content += get_nav_footer()
        return content
    content += "[bold white]Welcome! 🐶[/bold white]\n\n"
    content += "[cyan]Quick setup:[/cyan]\n"
    content += "  1. Pick your model provider\n"
    content += "  2. Optional: MCP servers\n"
    content += "  3. Learn when to use which agent\n"
    content += "  4. Start coding!\n\n"
    content += "[dim]Takes ~1 minute. Let's go![/dim]"
    content += get_nav_footer()
    return content


def slide_models(selected_option: int, options: List[Tuple[str, str]]) -> str:
    """Slide 2: Model selection."""
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        content = "[bold cyan]选择模型[/bold cyan]\n\n"
        content += "[white]你希望如何访问大模型？[/white]\n\n"
        labels = {
            "chatgpt": "ChatGPT 订阅",
            "claude": "Claude Code 订阅",
            "api_keys": "API 密钥",
            "openrouter": "OpenRouter",
            "skip": "暂时跳过",
        }
        for i, (option_id, label) in enumerate(options):
            display = labels.get(option_id, label)
            content += (
                f"[bold green]▶ {display}[/bold green]\n"
                if i == selected_option
                else f"[dim]  {display}[/dim]\n"
            )
        content += "\n[dim]中国区模型可稍后通过 /cn-setup 配置。[/dim]\n"
        content += get_nav_footer()
        return content
    content = "[bold cyan]📦 Pick Your Models[/bold cyan]\n\n"
    content += "[white]How do you want to access LLMs?[/white]\n\n"

    for i, (_, label) in enumerate(options):
        if i == selected_option:
            content += f"[bold green]▶ {label}[/bold green]\n"
        else:
            content += f"[dim]  {label}[/dim]\n"

    content += "\n"

    # Context based on selection
    opt = options[selected_option][0] if options else None
    if opt == "chatgpt":
        content += "[yellow]💡 ChatGPT OAuth[/yellow]\n"
        content += "  Uses your existing subscription\n"
        content += "  GPT-5.2, GPT-5.2-codex\n"
    elif opt == "claude":
        content += "[yellow]💡 Claude OAuth[/yellow]\n"
        content += "  Uses your existing subscription\n"
        content += "  Opus/Sonnet/Haiku 4.5\n"
    elif opt == "api_keys":
        content += "[yellow]💡 API Keys[/yellow]\n"
        content += "  [cyan]/set OPENAI_API_KEY=sk-...[/cyan]\n"
        content += "  [cyan]/add_model[/cyan] to browse 1500+ models\n"
    elif opt == "openrouter":
        content += "[yellow]💡 OpenRouter[/yellow]\n"
        content += "  One API key, all providers\n"
        content += "  [cyan]/set OPENROUTER_API_KEY=...[/cyan]\n"
    else:
        content += "[dim]No worries! Use /set or /add_model later[/dim]\n"

    content += get_nav_footer()
    return content


def slide_mcp() -> str:
    """Slide 3: MCP servers (optional power-ups)."""
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        return (
            "[bold cyan]MCP 服务（可选）[/bold cyan]\n\n"
            "[white]通过外部工具扩展能力。[/white]\n\n"
            "[green]命令：[/green]\n"
            "  [cyan]/mcp install[/cyan]  浏览目录\n"
            "  [cyan]/mcp list[/cyan]     查看服务\n\n"
            "[dim]只想编码时可以直接跳过。[/dim]" + get_nav_footer()
        )
    content = "[bold cyan]🔌 MCP Servers (Optional)[/bold cyan]\n\n"
    content += "[white]Supercharge with external tools![/white]\n\n"
    content += "[green]Commands:[/green]\n"
    content += "  [cyan]/mcp install[/cyan]  Browse catalog\n"
    content += "  [cyan]/mcp list[/cyan]     See your servers\n\n"
    content += "[yellow]🌟 Popular picks:[/yellow]\n"
    content += "  • GitHub integration\n"
    content += "  • Postgres/databases\n"
    content += "  • Slack, Linear, etc.\n\n"
    content += "[dim]Skip this if you just want to code![/dim]"
    content += get_nav_footer()
    return content


def slide_use_cases() -> str:
    """Slide 4: When to use which agent - THE IMPORTANT ONE."""
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        return (
            "[bold cyan]如何选择智能体[/bold cyan]\n\n"
            "[bold yellow]Code Puppy（默认）[/bold yellow]\n"
            "  适合直接编码、修复缺陷、重构和编写测试。\n\n"
            "[bold yellow]Planning Agent[/bold yellow]\n"
            "  适合复杂、多步骤和跨文件项目。\n\n"
            "[cyan]切换命令：/agent planning-agent[/cyan]" + get_nav_footer()
        )
    content = "[bold cyan]🎯 When to Use What[/bold cyan]\n\n"

    content += "[bold yellow]🐶 Code Puppy (default)[/bold yellow]\n"
    content += "  [green]USE FOR:[/green] Direct coding tasks\n"
    content += "  • Fix this bug\n"
    content += "  • Add a feature to this file\n"
    content += "  • Refactor this function\n"
    content += "  • Write tests for X\n\n"

    content += "[bold yellow]📋 Planning Agent[/bold yellow]\n"
    content += "  [green]USE FOR:[/green] Complex multi-step projects\n"
    content += "  • Build me a REST API with auth\n"
    content += "  • Create a CLI tool from scratch\n"
    content += "  • Refactor entire codebase\n"
    content += "  • Multi-file architectural changes\n\n"

    content += "[cyan]Switch: /agent planning-agent[/cyan]\n"
    content += "[dim]Planning breaks big tasks into steps,[/dim]\n"
    content += "[dim]then delegates to specialists.[/dim]"
    content += get_nav_footer()
    return content


def slide_done(trigger_oauth: str | None) -> str:
    """Slide 5: You're ready!"""
    from code_puppy.i18n import get_locale

    if get_locale() == "zh-CN":
        return (
            "[bold green]准备完成！[/bold green]\n\n"
            "[bold cyan]常用命令：[/bold cyan]\n"
            "  [cyan]/model[/cyan]   切换模型\n"
            "  [cyan]/agent[/cyan]   切换智能体\n"
            "  [cyan]/help[/cyan]    查看全部命令\n"
            "  [cyan]/cn-setup[/cyan] 配置中国区模型\n\n"
            "[bold yellow]按 Enter 开始编码。[/bold yellow]" + get_nav_footer()
        )
    content = "[bold green]🎉 Ready to Roll![/bold green]\n\n"
    content += "[bold cyan]Essential commands:[/bold cyan]\n"
    content += "  [cyan]/model[/cyan]   Switch models\n"
    content += "  [cyan]/agent[/cyan]   Switch agents\n"
    content += "  [cyan]/help[/cyan]    All commands\n\n"

    content += "[bold yellow]Pro tips:[/bold yellow]\n"
    content += "  • Be specific in prompts\n"
    content += "  • Use Planning Agent for big tasks\n"
    content += "  • @ for file path completion\n\n"

    if trigger_oauth:
        content += f"[bold cyan]→ {trigger_oauth.title()} OAuth next![/bold cyan]\n\n"

    content += "[dim]Re-run anytime: [/dim][cyan]/tutorial[/cyan]\n"
    content += "\n[bold yellow]Press Enter to start coding! 🐶[/bold yellow]"
    content += get_nav_footer()
    return content
