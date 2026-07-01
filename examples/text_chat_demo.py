"""Run a text chat demo from a profile config."""

import argparse

from mini_agent.config.loader import load_profile_config
from mini_agent.interaction.text_cli import TextCLI
from mini_agent.models.factory import build_agent_from_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="local")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    config = load_profile_config(args.config_dir, args.profile)
    TextCLI(build_agent_from_profile(config)).run()


if __name__ == "__main__":
    main()
