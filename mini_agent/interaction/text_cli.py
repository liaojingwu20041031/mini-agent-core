"""Text CLI interaction."""

from __future__ import annotations

from mini_agent.core.agent import Agent


class TextCLI:
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def run(self) -> None:
        print("mini-agent text CLI. Commands: /exit, /reset, /tools")
        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input == "/exit":
                break
            if user_input == "/reset":
                self.agent.reset()
                print("session reset")
                continue
            if user_input == "/tools":
                for item in self.agent.tools.list():
                    print(f"- {item.name} [{item.risk_level}] {item.description}")
                continue
            print(self.agent.run(user_input))

