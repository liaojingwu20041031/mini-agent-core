"""Kimi/Moonshot text chat demo.

Set MOONSHOT_API_KEY or LLM_API_KEY before running.
"""

import os

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.core.agent import Agent
from mini_agent.core.config import load_config, parse_extra_body
from mini_agent.interaction.text_cli import TextCLI


def main() -> None:
    config = load_config()
    llm = OpenAICompatibleClient.from_provider(
        provider="kimi",
        api_key=os.getenv("MOONSHOT_API_KEY") or config.llm_api_key,
        model=config.llm_model,
        timeout=config.llm_timeout,
        temperature=config.llm_temperature,
        extra_body=parse_extra_body(config),
    )
    TextCLI(Agent(llm=llm, max_steps=config.agent_max_steps, llm_timeout=config.llm_timeout)).run()


if __name__ == "__main__":
    main()
