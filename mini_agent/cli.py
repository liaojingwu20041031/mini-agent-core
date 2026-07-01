"""Command line interface for Mini Agent Core."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from mini_agent.config.env import env_status
from mini_agent.config.loader import CONFIG_FILES, load_profile_config
from mini_agent.config.validator import validate_profile_config
from mini_agent.core.status import ConsoleStatusSink, NullStatusSink
from mini_agent.core.trace import configure_logging
from mini_agent.interaction.text_cli import TextCLI
from mini_agent.mcp.manager import MCPManager
from mini_agent.models.factory import build_agent_from_profile
from mini_agent.skills.registry import build_tool_registry
from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.voice.audio_input import TextAudioInput
from mini_agent.voice.audio_output import TextAudioOutput
from mini_agent.voice.pipeline import VoicePipeline


PROFILE_HINTS = {
    "qwen": {
        "name": "阿里云百炼 / DashScope",
        "env": "DASHSCOPE_API_KEY",
        "model": "qwen.main.model，例如 qwen-plus",
        "note": "QWEN_API_KEY 不是默认变量名；如果你用 DeepSeek Key，请改用 --profile deepseek。",
    },
    "deepseek": {
        "name": "DeepSeek",
        "env": "DEEPSEEK_API_KEY",
        "model": "deepseek.main.model，例如 deepseek-chat",
        "note": "DeepSeek Key 只配 deepseek profile，不会被 qwen profile 使用。",
    },
    "kimi": {
        "name": "Moonshot Kimi",
        "env": "MOONSHOT_API_KEY",
        "model": "kimi.main.model，例如 kimi-k2.6",
        "note": "",
    },
    "glm": {
        "name": "智谱 GLM",
        "env": "ZHIPUAI_API_KEY",
        "model": "glm.main.model，例如 glm-4.5",
        "note": "",
    },
    "siliconflow": {
        "name": "硅基流动",
        "env": "SILICONFLOW_API_KEY",
        "model": "siliconflow.main.model，例如 deepseek-ai/DeepSeek-V3.1",
        "note": "",
    },
    "remote": {
        "name": "OpenAI 或其他远程兼容服务",
        "env": "OPENAI_API_KEY",
        "model": "remote.main.model，例如 gpt-4o-mini",
        "note": "",
    },
    "local": {
        "name": "本地 OpenAI-compatible 服务",
        "env": "",
        "model": "local.main.model，例如 qwen2.5:7b",
        "note": "本地模型通常不需要 API Key，但要先启动 Ollama、LM Studio 或 llama.cpp server。",
    },
}


class ChineseArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("add_help", False)
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助")
        self._positionals.title = "位置参数"
        self._optionals.title = "选项"


def _redacted(config) -> dict[str, Any]:
    data = asdict(config)
    for provider in data["providers"].values():
        env_name = provider.get("api_key_env", "")
        provider["api_key"] = env_status(env_name) if env_name else {"env": "", "present": False}
    for role in data["models"].values():
        env_name = role.get("api_key_env", "")
        if env_name:
            role["api_key"] = env_status(env_name)
    data.pop("raw", None)
    return data


def config_check(args: argparse.Namespace) -> int:
    try:
        config = load_profile_config(args.config_dir, args.profile)
    except Exception as exc:
        print(f"配置错误：{exc}")
        return 2
    errors = validate_profile_config(config)
    if errors:
        print(f"profile {args.profile!r} 有 {len(errors)} 个问题：")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"profile {args.profile!r} 配置有效")
    return 0


def config_show(args: argparse.Namespace) -> int:
    try:
        config = load_profile_config(args.config_dir, args.profile)
    except Exception as exc:
        print(f"配置错误：{exc}")
        return 2
    print(json.dumps(_redacted(config), ensure_ascii=False, indent=2, default=str))
    return 0


def _print_validation_errors(profile: str, errors: list[str], action: str) -> None:
    print(f"{action}失败：profile {profile!r} 配置未通过检查。")
    for error in errors:
        print(f"- {error}")
    print(f"请先运行：mini-agent config check --profile {profile}")


def init_config(args: argparse.Namespace) -> int:
    root = Path(args.config_dir)
    root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for name in CONFIG_FILES:
        source = root / f"{name}.yaml.example"
        target = root / f"{name}.yaml"
        if not source.exists():
            missing.append(str(source))
            continue
        if target.exists() and not args.force:
            skipped.append(str(target))
            continue
        shutil.copyfile(source, target)
        copied.append(str(target))

    quickstart_source = root / "quickstart.yaml.example"
    quickstart_target = root / "quickstart.yaml"
    if quickstart_source.exists():
        if quickstart_target.exists() and not args.force:
            skipped.append(str(quickstart_target))
        else:
            shutil.copyfile(quickstart_source, quickstart_target)
            copied.append(str(quickstart_target))

    if copied:
        print("已初始化配置文件：")
        for item in copied:
            print(f"- {item}")
    if skipped:
        print("以下文件已存在，未覆盖（如需覆盖请加 --force）：")
        for item in skipped:
            print(f"- {item}")
    if missing:
        print("以下示例文件不存在，请检查仓库：")
        for item in missing:
            print(f"- {item}")
        return 1

    hint = PROFILE_HINTS.get(
        args.profile,
        {"name": args.profile, "env": "", "model": f"{args.profile}.main.model", "note": ""},
    )
    env_name = hint["env"]
    model_hint = hint["model"]
    print("\n下一步：")
    print(f"你选择的 profile 是 {args.profile!r}（{hint['name']}）。")
    if env_name:
        print(f"1. 设置环境变量 {env_name}=你的 API Key（不要写进 YAML）。")
    else:
        print("1. 确认本地 OpenAI-compatible 服务已启动，例如 Ollama 或 LM Studio。")
    print(f"2. 编辑 {root / 'models.yaml'}，填写 {model_hint}。")
    print(f"3. 运行 mini-agent config check --profile {args.profile}")
    print(f"4. 运行 mini-agent text --profile {args.profile}")
    if hint["note"]:
        print(f"提示：{hint['note']}")
    return 0


def text_mode(args: argparse.Namespace) -> int:
    configure_logging(args.debug)
    try:
        config = load_profile_config(args.config_dir, args.profile)
        errors = validate_profile_config(config)
        if errors:
            _print_validation_errors(args.profile, errors, "启动文本模式")
            return 1
        sink = NullStatusSink() if args.no_status else ConsoleStatusSink()
        agent = build_agent_from_profile(config, status_sink=sink)
    except Exception as exc:
        print(f"启动文本模式失败：{exc}")
        return 2
    TextCLI(agent).run()
    return 0


def voice_mode(args: argparse.Namespace) -> int:
    configure_logging(args.debug)
    try:
        config = load_profile_config(args.config_dir, args.profile)
        errors = validate_profile_config(config)
        if errors:
            _print_validation_errors(args.profile, errors, "启动语音模式")
            return 1
        sink = NullStatusSink() if args.no_status else ConsoleStatusSink()
        agent = build_agent_from_profile(config, status_sink=sink)
    except Exception as exc:
        print(f"启动语音模式失败：{exc}")
        return 2
    pipeline = VoicePipeline(
        audio_input=TextAudioInput(lambda: input("say> ")),
        stt_engine=DummySTT(),
        agent=agent,
        tts_engine=DummyTTS(),
        audio_output=TextAudioOutput(),
    )
    print("mini-agent dummy 语音模式。直接输入文字模拟语音，输入 /exit 退出。")
    while True:
        command = input("Enter 继续，/exit 退出> ").strip()
        if command == "/exit":
            break
        pipeline.run_once()
    return 0


def tools_list(args: argparse.Namespace) -> int:
    try:
        config = load_profile_config(args.config_dir, args.profile)
        registry = build_tool_registry(config.tools.enabled)
    except Exception as exc:
        print(f"读取工具配置失败：{exc}")
        return 2
    print(f"profile {args.profile!r} 启用的工具：")
    for tool in registry.list():
        print(f"- {tool.name}\t[{tool.risk_level}]\t{tool.description}")
    return 0


def _load_mcp_profile(config_dir: str | Path, profile: str) -> dict[str, Any]:
    path = Path(config_dir) / "mcp.yaml"
    if not path.exists():
        raise FileNotFoundError(f"缺少 MCP 配置文件：{path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profiles = data.get("profiles")
    if isinstance(profiles, dict):
        if profile not in profiles:
            available = ", ".join(sorted(profiles))
            raise ValueError(f"未知 MCP profile {profile!r}，可选：{available}")
        return profiles.get(profile) or {}
    return data


def mcp_list(args: argparse.Namespace) -> int:
    try:
        profile_config = _load_mcp_profile(args.config_dir, args.profile)
        manager = MCPManager(profile_config)
    except Exception as exc:
        print(f"读取 MCP 配置失败：{exc}")
        return 2
    print(f"MCP profile {args.profile!r}:")
    if not manager.servers:
        print("- 未配置 MCP server")
        return 0
    for server in manager.servers.values():
        enabled = "enabled=true" if server.enabled else "enabled=false"
        command = server.command or "-"
        sandbox = server.sandbox or "-"
        print(f"- {server.name}\t{enabled}\t[{server.risk_level}]\tcommand={command}\tsandbox={sandbox}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = ChineseArgumentParser(prog="mini-agent", description="轻量 AI Agent 核心模板 CLI")
    sub = parser.add_subparsers(dest="command", parser_class=ChineseArgumentParser)

    init = sub.add_parser("init", help="从示例文件初始化配置")
    init.add_argument("--profile", default="local", help="初始化后准备使用的 profile")
    init.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    init.add_argument("--force", action="store_true", help="覆盖已存在的配置文件")
    init.set_defaults(func=init_config)

    text = sub.add_parser("text", help="启动文本交互模式")
    text.add_argument("--profile", default="local", help="使用的 profile")
    text.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    text.add_argument("--no-status", action="store_true", help="关闭简洁状态显示")
    text.add_argument("--debug", action="store_true", help="开启详细调试日志")
    text.set_defaults(func=text_mode)

    voice = sub.add_parser("voice", help="启动 dummy 语音模式")
    voice.add_argument("--profile", default="local", help="使用的 profile")
    voice.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    voice.add_argument("--no-status", action="store_true", help="关闭简洁状态显示")
    voice.add_argument("--debug", action="store_true", help="开启详细调试日志")
    voice.set_defaults(func=voice_mode)

    tools = sub.add_parser("tools", help="查看内置工具")
    tools_sub = tools.add_subparsers(dest="tools_command", parser_class=ChineseArgumentParser)
    tools_list_cmd = tools_sub.add_parser("list", help="列出当前 profile 启用的工具")
    tools_list_cmd.add_argument("--profile", default="local", help="使用的 profile")
    tools_list_cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    tools_list_cmd.set_defaults(func=tools_list)

    mcp = sub.add_parser("mcp", help="查看 MCP 配置")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", parser_class=ChineseArgumentParser)
    mcp_list_cmd = mcp_sub.add_parser("list", help="列出 MCP server，不启动进程")
    mcp_list_cmd.add_argument("--profile", default="online", help="MCP profile")
    mcp_list_cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    mcp_list_cmd.set_defaults(func=mcp_list)

    config = sub.add_parser("config", help="检查或显示 profile 配置")
    config_sub = config.add_subparsers(dest="config_command", parser_class=ChineseArgumentParser)
    for name, func in (("check", config_check), ("show", config_show)):
        help_text = "检查配置是否可运行" if name == "check" else "显示脱敏后的配置"
        cmd = config_sub.add_parser(name, help=help_text)
        cmd.add_argument("--profile", default="local", help="使用的 profile")
        cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
        cmd.set_defaults(func=func)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
