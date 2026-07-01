"""Run a text chat demo with an OpenAI-compatible model."""

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.builtin_tools import register_builtin_tools
from mini_agent.core.agent import Agent
from mini_agent.core.config import load_config
from mini_agent.core.guard import ToolGuard
from mini_agent.core.tools import ToolRegistry
from mini_agent.interaction.text_cli import TextCLI


def confirm(name: str, arguments: dict) -> bool:
    answer = input(f"Confirm tool {name} with {arguments}? [y/N] ").strip().lower()
    return answer == "y"


def main() -> None:
    config = load_config()
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = OpenAICompatibleClient(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model,
        timeout=config.llm_timeout,
        temperature=config.llm_temperature,
    )
    agent = Agent(
        llm=llm,
        tools=registry,
        max_steps=config.agent_max_steps,
        llm_timeout=config.llm_timeout,
        guard=ToolGuard(confirm_callback=confirm, allow_danger=config.allow_danger_tools),
    )
    TextCLI(agent).run()


if __name__ == "__main__":
    main()

