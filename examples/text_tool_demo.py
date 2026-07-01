"""Offline tool-call demo with a fake LLM."""

from mini_agent.builtin_tools import register_builtin_tools
from mini_agent.core.agent import Agent
from mini_agent.core.llm import LLMResponse
from mini_agent.core.messages import ToolCall
from mini_agent.core.tools import ToolRegistry


class FakeToolLLM:
    def __init__(self) -> None:
        self.calls = 0

    def chat(self, messages, tools=None, timeout=None):
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(tool_calls=[ToolCall(id="1", name="calculate", arguments={"expression": "2 + 3"})])
        return LLMResponse(content="2 + 3 = 5")


def main() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    agent = Agent(llm=FakeToolLLM(), tools=registry)
    print(agent.run("calculate 2 + 3"))


if __name__ == "__main__":
    main()

