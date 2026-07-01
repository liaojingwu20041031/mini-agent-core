"""Command line interface for Mini Agent Core."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from mini_agent.config.env import env_status
from mini_agent.config.loader import CONFIG_FILES, OPTIONAL_INIT_FILES, load_profile_config
from mini_agent.config.validator import validate_profile_config
from mini_agent.core.agent_spec import load_agent_spec
from mini_agent.core.state import MiniAgentState, load_state, save_state, state_path
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
        "service_name": "阿里云百炼 / DashScope",
        "api_key_env": "DASHSCOPE_API_KEY",
        "model_path": "config/models.yaml -> profiles.qwen.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "deepseek": {
        "service_name": "DeepSeek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_path": "config/models.yaml -> profiles.deepseek.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "kimi": {
        "service_name": "Moonshot Kimi",
        "api_key_env": "MOONSHOT_API_KEY",
        "model_path": "config/models.yaml -> profiles.kimi.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "glm": {
        "service_name": "智谱 GLM",
        "api_key_env": "ZHIPUAI_API_KEY",
        "model_path": "config/models.yaml -> profiles.glm.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "siliconflow": {
        "service_name": "硅基流动",
        "api_key_env": "SILICONFLOW_API_KEY",
        "model_path": "config/models.yaml -> profiles.siliconflow.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "remote": {
        "service_name": "OpenAI 或其他远程兼容服务",
        "api_key_env": "OPENAI_API_KEY",
        "model_path": "config/models.yaml -> profiles.remote.roles.main.model",
        "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
    },
    "local": {
        "service_name": "本地 OpenAI-compatible 服务",
        "api_key_env": "",
        "model_path": "config/models.yaml -> profiles.local.roles.main.model",
        "note": "本地模型通常不需要 API Key，但要先启动本地 OpenAI-compatible 服务。",
    },
}


class ChineseArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("add_help", False)
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助")
        self._positionals.title = "位置参数"
        self._optionals.title = "选项"


def _redacted(config, show_model: bool = False, show_examples: bool = False) -> dict[str, Any]:
    data = asdict(config)
    for provider in data["providers"].values():
        env_name = provider.get("api_key_env", "")
        provider["api_key"] = env_status(env_name) if env_name else {"env": "", "present": False}
        if not show_examples:
            provider.pop("example_models", None)
        elif provider.get("example_models"):
            provider["example_models_note"] = "仅文档参考，不参与运行。"
    for role in data["models"].values():
        env_name = role.get("api_key_env", "")
        if env_name:
            role["api_key"] = env_status(env_name)
        if "model" in role and not show_model:
            role["model"] = "<已配置>" if str(role.get("model", "")).strip() else "<未配置>"
    data.pop("raw", None)
    return data


def _model_config_path(profile: str, role: str = "main") -> str:
    return f"config/models.yaml -> profiles.{profile}.roles.{role}.model"


def _main_model_context(config_dir: str | Path, profile: str) -> tuple[Any, Any, Any, str, str]:
    config = load_profile_config(config_dir, profile)
    role = config.role("main")
    provider = config.providers.get(role.provider)
    if provider is None:
        raise KeyError(f"main.provider {role.provider!r} 未配置")
    base_url = role.base_url or provider.base_url
    api_key_env = role.api_key_env or provider.api_key_env
    return config, role, provider, base_url, api_key_env


def _models_endpoint(base_url: str) -> str:
    clean = base_url.rstrip("/")
    if clean.endswith("/v1"):
        return f"{clean}/models"
    return f"{clean}/v1/models"


def _fetch_remote_model_ids(base_url: str, api_key: str, timeout: float = 15) -> tuple[list[str], str | None]:
    try:
        import httpx
    except ImportError as exc:
        return [], f"缺少 httpx：{exc}"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = _models_endpoint(base_url)
    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:
        return [], f"网络错误：{exc}"
    if response.status_code >= 400:
        return [], f"HTTP {response.status_code}: {response.text[:300]}"
    try:
        payload = response.json()
    except ValueError as exc:
        return [], f"响应不是 JSON：{exc}"
    items = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return [], "服务返回中没有 data 列表；该 provider 可能不支持 /models。"
    ids = [str(item.get("id", "")).strip() for item in items if isinstance(item, dict) and str(item.get("id", "")).strip()]
    return ids, None


def _write_model_id(config_dir: str | Path, profile: str, model_id: str) -> None:
    path = Path(config_dir) / "models.yaml"
    if not path.exists():
        raise FileNotFoundError(f"缺少配置文件：{path}。请先运行 mini-agent init --profile {profile}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profiles = data.setdefault("profiles", {})
    profile_data = profiles.setdefault(profile, {})
    roles = profile_data.setdefault("roles", {})
    main = roles.setdefault("main", {})
    main["model"] = model_id
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _load_agent_spec_or_none(config_dir: str | Path, agent_name: str):
    try:
        return load_agent_spec(config_dir, agent_name)
    except FileNotFoundError:
        return None


def _resolve_profile_agent(args: argparse.Namespace) -> tuple[str, str, str]:
    state = load_state()
    profile = getattr(args, "profile", None) or (state.default_profile if state else "")
    agent_name = getattr(args, "agent", None) or (state.default_agent if state else "default")
    config_dir = getattr(args, "config_dir", None) or (state.config_dir if state else "config")
    if not profile:
        print("未找到默认 profile。请先运行：")
        print("mini-agent init --profile <profile>")
        print("mini-agent use --profile <profile> --agent default")
        raise ValueError("missing_profile")
    return profile, agent_name, config_dir


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
    print(json.dumps(_redacted(config, show_model=args.show_model, show_examples=args.show_examples), ensure_ascii=False, indent=2, default=str))
    return 0


def config_where(args: argparse.Namespace) -> int:
    print("主模型配置位置：" if args.role == "main" else "模型配置位置：")
    print(_model_config_path(args.profile, args.role))
    print("\n请填写你的服务商控制台或本地模型服务提供的模型 ID。")
    return 0


def _print_validation_errors(profile: str, errors: list[str], action: str) -> None:
    print(f"{action}失败：profile {profile!r} 配置未通过检查。")
    for error in errors:
        print(f"- {error}")
    print(f"请先运行：mini-agent config check --profile {profile}")


def models_list(args: argparse.Namespace) -> int:
    try:
        _config, _role, provider, base_url, api_key_env = _main_model_context(args.config_dir, args.profile)
    except Exception as exc:
        print(f"读取模型配置失败：{exc}")
        return 2
    print(f"profile: {args.profile}")
    print(f"provider: {provider.name}")
    print(f"api_key_env: {api_key_env or '<无>'}")
    print(f"model config path: {_model_config_path(args.profile)}")
    if not base_url:
        print(f"base_url 缺失，请检查 config/providers.yaml -> profiles.{args.profile}.providers.{provider.name}.base_url")
        return 1
    if api_key_env and not os.getenv(api_key_env):
        print(f"API Key 缺失，请设置环境变量：{api_key_env}")
        return 1
    ids, error = _fetch_remote_model_ids(base_url, os.getenv(api_key_env, "") if api_key_env else "")
    if error:
        print(f"/models 查询失败：{error}")
        return 1
    print("\n服务返回的模型 ID：")
    for index, model_id in enumerate(ids, start=1):
        print(f"{index}. {model_id}")
    print(f"\n选择后运行：mini-agent models use --profile {args.profile} --model \"<模型ID>\"")
    return 0


def models_use(args: argparse.Namespace) -> int:
    if not args.model.strip():
        print("--model 不能为空")
        return 1
    try:
        _write_model_id(args.config_dir, args.profile, args.model.strip())
    except Exception as exc:
        print(f"写入模型配置失败：{exc}")
        return 2
    print(f"已写入：{_model_config_path(args.profile)}")
    print(f"后续建议运行：mini-agent config check --profile {args.profile}")
    print(f"然后运行：mini-agent use --profile {args.profile} --agent default")
    print("最后运行：mini-agent start")
    return 0


def models_check(args: argparse.Namespace) -> int:
    try:
        _config, role, _provider, _base_url, _api_key_env = _main_model_context(args.config_dir, args.profile)
    except Exception as exc:
        print(f"读取模型配置失败：{exc}")
        return 2
    print(f"模型配置位置：{_model_config_path(args.profile)}")
    if not role.model.strip():
        print("[ERROR] main.model 未配置。请填写服务商控制台或 /models 返回的模型 ID。")
        return 1
    print("[OK] main.model 已配置。")
    return 0


def models_doctor(args: argparse.Namespace) -> int:
    status = 0
    try:
        _config, role, provider, base_url, api_key_env = _main_model_context(args.config_dir, args.profile)
        print(f"[OK] provider 已配置：{provider.name}")
    except Exception as exc:
        print(f"[ERROR] provider 检查失败：{exc}")
        return 1
    if base_url:
        print("[OK] base_url 已配置")
    else:
        print(f"[ERROR] base_url 缺失：config/providers.yaml -> profiles.{args.profile}.providers.{provider.name}.base_url")
        status = 1
    if api_key_env:
        print(f"[OK] api_key_env 已配置：{api_key_env}")
        if os.getenv(api_key_env):
            print("[OK] API Key 环境变量已设置")
        else:
            print(f"[ERROR] API Key 环境变量未设置：{api_key_env}")
            status = 1
    else:
        print("[WARN] api_key_env 为空，适用于无需 Key 的本地服务")
    remote_ids: list[str] = []
    if base_url and (not api_key_env or os.getenv(api_key_env)):
        remote_ids, error = _fetch_remote_model_ids(base_url, os.getenv(api_key_env, "") if api_key_env else "")
        if error:
            print(f"[WARN] /models 查询失败：{error}")
        else:
            print(f"[OK] /models 查询成功，返回 {len(remote_ids)} 个模型 ID")
    if role.model.strip():
        print("[OK] main.model 已配置")
        if remote_ids and role.model not in remote_ids:
            print("[WARN] 当前 main.model 不在 /models 返回列表中，请确认服务端是否支持该模型 ID。")
    else:
        print(f"[ERROR] main.model 未配置：{_model_config_path(args.profile)}")
        status = 1
    if status:
        print("\n修复步骤：")
        print(f"1. mini-agent models list --profile {args.profile}")
        print(f"2. mini-agent models use --profile {args.profile} --model \"<模型ID>\"")
        print(f"3. mini-agent config check --profile {args.profile}")
    return status


def init_wizard(args: argparse.Namespace) -> int:
    print("\n初始化向导：")
    hint = PROFILE_HINTS.get(args.profile)
    if hint:
        print(f"服务：{hint['service_name']}")
        print(f"API Key 环境变量：{hint['api_key_env'] or '<无>'}")
        print(f"模型配置路径：{hint['model_path']}")
    try:
        _config, role, _provider, base_url, api_key_env = _main_model_context(args.config_dir, args.profile)
    except Exception as exc:
        print(f"无法读取 profile 配置：{exc}")
        return 1
    ids: list[str] = []
    if api_key_env and not os.getenv(api_key_env):
        print(f"API Key 未设置，跳过 /models 查询：{api_key_env}")
    elif base_url:
        ids, error = _fetch_remote_model_ids(base_url, os.getenv(api_key_env, "") if api_key_env else "")
        if error:
            print(f"/models 查询失败，改为手动步骤：{error}")
        elif ids:
            print("服务返回的模型 ID：")
            for index, model_id in enumerate(ids, start=1):
                print(f"{index}. {model_id}")
    if sys.stdin.isatty() and (ids or True):
        choice = input("输入序号选择模型，输入 m 手动填写，输入 s 跳过> ").strip()
        selected = ""
        if choice.lower() == "m":
            selected = input("请输入模型 ID> ").strip()
        elif choice.lower() == "s" or not choice:
            selected = ""
        elif choice.isdigit() and ids and 1 <= int(choice) <= len(ids):
            selected = ids[int(choice) - 1]
        if selected:
            _write_model_id(args.config_dir, args.profile, selected)
            role.model = selected
            print(f"已写入：{_model_config_path(args.profile)}")
    else:
        print(f"非交互模式：请运行 mini-agent models use --profile {args.profile} --model \"<模型ID>\"")
    return config_check(args)


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

    for name in OPTIONAL_INIT_FILES:
        source = root / f"{name}.yaml.example"
        target = root / f"{name}.yaml"
        if not source.exists():
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
        {
            "service_name": args.profile,
            "api_key_env": "",
            "model_path": _model_config_path(args.profile),
            "note": "模型名称请以服务商控制台或 models list 返回结果为准。",
        },
    )
    env_name = hint["api_key_env"]
    print("\n下一步：")
    print(f"你选择的 profile 是 {args.profile!r}（{hint['service_name']}）。")
    if env_name:
        print(f"1. 设置环境变量 {env_name}=你的 API Key（不要写进 YAML）。")
    else:
        print("1. 确认本地 OpenAI-compatible 服务已启动。")
    print(f"2. 可运行 mini-agent models list --profile {args.profile} 查询服务端模型 ID。")
    print(f"3. 编辑 {root / 'models.yaml'}，填写 {_model_config_path(args.profile)}，或运行 models use 写入。")
    print(f"4. 运行 mini-agent config check --profile {args.profile}")
    print(f"5. 运行 mini-agent use --profile {args.profile} --agent default")
    print("6. 运行 mini-agent start")
    if hint["note"]:
        print(f"提示：{hint['note']}")
    if args.wizard:
        return init_wizard(args)
    return 0


def text_mode(args: argparse.Namespace) -> int:
    configure_logging(args.debug)
    try:
        profile = args.profile
        agent_name = getattr(args, "agent", "default")
        config = load_profile_config(args.config_dir, profile)
        errors = validate_profile_config(config)
        if errors:
            _print_validation_errors(profile, errors, "启动文本模式")
            return 1
        sink = NullStatusSink() if args.no_status else ConsoleStatusSink()
        agent_spec = load_agent_spec(args.config_dir, agent_name)
        agent = build_agent_from_profile(config, status_sink=sink, agent_spec=agent_spec)
    except Exception as exc:
        print(f"启动文本模式失败：{exc}")
        return 2
    TextCLI(agent).run()
    return 0


def voice_mode(args: argparse.Namespace) -> int:
    configure_logging(args.debug)
    try:
        profile = args.profile
        agent_name = getattr(args, "agent", "default")
        config = load_profile_config(args.config_dir, profile)
        errors = validate_profile_config(config)
        if errors:
            _print_validation_errors(profile, errors, "启动语音模式")
            return 1
        sink = NullStatusSink() if args.no_status else ConsoleStatusSink()
        agent_spec = load_agent_spec(args.config_dir, agent_name)
        agent = build_agent_from_profile(config, status_sink=sink, agent_spec=agent_spec)
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
        registry = build_tool_registry(config.tools)
    except Exception as exc:
        print(f"读取工具配置失败：{exc}")
        return 2
    print(f"profile {args.profile!r} 启用的工具：")
    for tool in registry.list():
        print(f"- {tool.name}\t[{tool.risk_level}]\t{tool.description}")
    return 0


def tools_describe(args: argparse.Namespace) -> int:
    try:
        config = load_profile_config(args.config_dir, args.profile)
        registry = build_tool_registry(config.tools)
        definition = registry.get(args.tool_name)
    except Exception as exc:
        print(f"读取工具配置失败：{exc}")
        return 2
    if definition is None:
        print(f"未知工具：{args.tool_name}")
        return 1
    print(f"name: {definition.name}")
    print(f"title: {definition.title or definition.name}")
    print(f"category: {definition.category}")
    print(f"namespace: {definition.namespace}")
    print(f"risk_level: {definition.risk_level}")
    print(f"description: {definition.description}")
    print(f"when_to_use: {definition.when_to_use}")
    print(f"when_not_to_use: {definition.when_not_to_use}")
    print("parameters:")
    print(json.dumps(definition.parameters, ensure_ascii=False, indent=2))
    if definition.examples:
        print("examples:")
        for example in definition.examples:
            print(f"- {example}")
    return 0


def use_profile(args: argparse.Namespace) -> int:
    state = MiniAgentState(
        default_profile=args.profile,
        default_agent=args.agent,
        default_mode=args.mode,
        config_dir=args.config_dir,
    )
    path = save_state(state)
    print(f"已保存默认启动配置：{path}")
    print(f"default_profile: {state.default_profile}")
    print(f"default_agent: {state.default_agent}")
    print(f"default_mode: {state.default_mode}")
    print(f"config_dir: {state.config_dir}")
    return 0


def start_mode(args: argparse.Namespace) -> int:
    try:
        profile, agent_name, config_dir = _resolve_profile_agent(args)
    except ValueError:
        return 1
    args.profile = profile
    args.agent = agent_name
    args.config_dir = config_dir
    if args.command == "speak":
        return voice_mode(args)
    return text_mode(args)


def status_command(args: argparse.Namespace) -> int:
    state = load_state()
    if state is None:
        print("未找到状态文件。请先运行：")
        print("mini-agent init --profile <profile>")
        print("mini-agent use --profile <profile> --agent default")
        return 1
    print(f"default_profile: {state.default_profile}")
    print(f"default_agent: {state.default_agent}")
    print(f"default_mode: {state.default_mode}")
    print(f"config_dir: {state.config_dir}")
    print(f"state_path: {state_path()}")
    try:
        config = load_profile_config(state.config_dir, state.default_profile)
        errors = validate_profile_config(config)
        if errors:
            print("配置检查结果：ERROR")
            for error in errors:
                print(f"- {error}")
        else:
            print("配置检查结果：OK")
        registry = build_tool_registry(config.tools)
        names = {tool.name for tool in registry.list()}
        print(f"启用工具数: {len(names)}")
        online = bool({"web_search", "fetch_url_text_public", "weather_open_meteo"} & names)
        print(f"safe 联网工具: {'启用' if online else '未启用'}")
    except Exception as exc:
        print(f"状态检查失败：{exc}")
        return 2
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
    init.add_argument("--wizard", action="store_true", help="初始化后进入模型配置向导")
    init.set_defaults(func=init_config)

    text = sub.add_parser("text", help="启动文本交互模式")
    text.add_argument("--profile", default="local", help="使用的 profile")
    text.add_argument("--agent", default="default", help="使用的 Agent 配置名")
    text.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    text.add_argument("--no-status", action="store_true", help="关闭简洁状态显示")
    text.add_argument("--debug", action="store_true", help="开启详细调试日志")
    text.set_defaults(func=text_mode)

    voice = sub.add_parser("voice", help="启动 dummy 语音模式")
    voice.add_argument("--profile", default="local", help="使用的 profile")
    voice.add_argument("--agent", default="default", help="使用的 Agent 配置名")
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
    tools_describe_cmd = tools_sub.add_parser("describe", help="显示工具元信息")
    tools_describe_cmd.add_argument("tool_name", help="工具名")
    tools_describe_cmd.add_argument("--profile", default="local", help="使用的 profile")
    tools_describe_cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    tools_describe_cmd.set_defaults(func=tools_describe)

    mcp = sub.add_parser("mcp", help="查看 MCP 配置")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", parser_class=ChineseArgumentParser)
    mcp_list_cmd = mcp_sub.add_parser("list", help="列出 MCP server，不启动进程")
    mcp_list_cmd.add_argument("--profile", default="online", help="MCP profile")
    mcp_list_cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    mcp_list_cmd.set_defaults(func=mcp_list)

    config = sub.add_parser("config", help="检查或显示 profile 配置")
    config_sub = config.add_subparsers(dest="config_command", parser_class=ChineseArgumentParser)
    for name, func in (("check", config_check), ("show", config_show), ("where", config_where)):
        help_text = "检查配置是否可运行" if name == "check" else "显示脱敏后的配置"
        if name == "where":
            help_text = "显示模型配置路径"
        cmd = config_sub.add_parser(name, help=help_text)
        cmd.add_argument("--profile", default="local", help="使用的 profile")
        cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
        if name == "show":
            cmd.add_argument("--show-model", action="store_true", help="显示用户已配置的模型名")
            cmd.add_argument("--show-examples", action="store_true", help="显示 provider 示例模型，仅供参考")
        if name == "where":
            cmd.add_argument("--role", default="main", help="模型角色")
        cmd.set_defaults(func=func)
    models = sub.add_parser("models", help="模型配置闭环")
    models_sub = models.add_subparsers(dest="models_command", parser_class=ChineseArgumentParser)
    for name, func, help_text in (
        ("list", models_list, "查询服务端 /models"),
        ("use", models_use, "写入用户选择的模型 ID"),
        ("check", models_check, "本地检查 main.model"),
        ("doctor", models_doctor, "诊断 provider、Key、/models 和 main.model"),
    ):
        cmd = models_sub.add_parser(name, help=help_text)
        cmd.add_argument("--profile", default="local", help="使用的 profile")
        cmd.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
        if name == "use":
            cmd.add_argument("--model", required=True, help="用户显式选择的模型 ID")
        cmd.set_defaults(func=func)

    use = sub.add_parser("use", help="保存默认 profile/agent，便于一键启动")
    use.add_argument("--profile", required=True, help="默认 profile")
    use.add_argument("--agent", default="default", help="默认 Agent")
    use.add_argument("--mode", default="text", choices=("text", "voice"), help="默认模式")
    use.add_argument("--config-dir", default=str(Path("config")), help="配置目录")
    use.set_defaults(func=use_profile)

    for name, help_text in (("start", "按 state 启动文本模式"), ("chat", "按 state 启动文本模式"), ("speak", "按 state 启动语音模式")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--profile", default=None, help="覆盖 state profile")
        cmd.add_argument("--agent", default=None, help="覆盖 state Agent")
        cmd.add_argument("--config-dir", default=None, help="覆盖 state 配置目录")
        cmd.add_argument("--no-status", action="store_true", help="关闭简洁状态显示")
        cmd.add_argument("--debug", action="store_true", help="开启详细调试日志")
        cmd.set_defaults(func=start_mode)

    status = sub.add_parser("status", help="显示默认启动状态和安全摘要")
    status.set_defaults(func=status_command)
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
