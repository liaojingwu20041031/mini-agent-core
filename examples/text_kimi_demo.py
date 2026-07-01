"""Kimi/Moonshot text chat demo. Set MOONSHOT_API_KEY before running."""

from mini_agent.config.loader import load_profile_config
from mini_agent.interaction.text_cli import TextCLI
from mini_agent.models.factory import build_agent_from_profile


def main() -> None:
    config = load_profile_config("config", "kimi")
    TextCLI(build_agent_from_profile(config)).run()


if __name__ == "__main__":
    main()
