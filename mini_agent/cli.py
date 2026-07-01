"""Command line interface for Mini Agent Core."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mini_agent.config.env import env_status
from mini_agent.config.loader import load_profile_config
from mini_agent.config.validator import validate_profile_config


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
        print(f"config error: {exc}")
        return 2
    errors = validate_profile_config(config)
    if errors:
        print(f"profile {args.profile!r} has {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"profile {args.profile!r} is valid")
    return 0


def config_show(args: argparse.Namespace) -> int:
    try:
        config = load_profile_config(args.config_dir, args.profile)
    except Exception as exc:
        print(f"config error: {exc}")
        return 2
    print(json.dumps(_redacted(config), ensure_ascii=False, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini-agent")
    sub = parser.add_subparsers(dest="command")
    config = sub.add_parser("config")
    config_sub = config.add_subparsers(dest="config_command")
    for name, func in (("check", config_check), ("show", config_show)):
        cmd = config_sub.add_parser(name)
        cmd.add_argument("--profile", default="local")
        cmd.add_argument("--config-dir", default=str(Path("config")))
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
