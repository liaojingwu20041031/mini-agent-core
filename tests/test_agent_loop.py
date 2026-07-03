import json

from mini_agent.core.agent import Agent
from mini_agent.core.llm import LLMResponse
from mini_agent.core.messages import ToolCall
from mini_agent.core.tools import ToolRegistry, tool


class SequenceLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def chat(self, messages, tools=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


@tool
def double(value: int):
    return value * 2


def test_agent_executes_tool_and_returns_final_answer():
    llm = SequenceLLM(
        [
            LLMResponse(tool_calls=[ToolCall(id="call-1", name="double", arguments={"value": 3})]),
            LLMResponse(content="The answer is 6."),
        ]
    )
    registry = ToolRegistry()
    registry.register(double)
    agent = Agent(llm=llm, tools=registry, max_steps=3)

    assert agent.run("double 3") == "The answer is 6."
    assert llm.calls == 2
    assert any(message.role == "tool" for message in agent.session.messages)


def test_agent_stops_at_max_steps():
    llm = SequenceLLM(
        [
            LLMResponse(tool_calls=[ToolCall(id="1", name="double", arguments={"value": 1})]),
            LLMResponse(tool_calls=[ToolCall(id="2", name="double", arguments={"value": 2})]),
            LLMResponse(content="Summary from completed tools."),
        ]
    )
    registry = ToolRegistry()
    registry.register(double)
    agent = Agent(llm=llm, tools=registry, max_steps=1)

    result = agent.run("loop")
    assert result == "Summary from completed tools."


def test_tool_result_truncation_keeps_valid_json():
    agent = Agent(llm=SequenceLLM([]), tool_result_max_chars=10)

    content = agent._truncate_tool_result(json.dumps({"name": "demo", "content": "x" * 100, "is_error": False, "error": None}))
    payload = json.loads(content)

    assert payload["truncated"] is True
    assert payload["name"] == "demo"
