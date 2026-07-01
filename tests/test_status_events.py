from mini_agent.core.agent import Agent
from mini_agent.core.llm import LLMResponse
from mini_agent.core.messages import ToolCall
from mini_agent.core.status import ListStatusSink
from mini_agent.core.tools import ToolRegistry, tool


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, messages, tools=None, timeout=None):
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@tool
def double(value: int) -> int:
    return value * 2


def test_status_events_cover_agent_llm_and_tool():
    sink = ListStatusSink()
    registry = ToolRegistry()
    registry.register(double)
    agent = Agent(
        llm=FakeLLM(
            [
                LLMResponse(tool_calls=[ToolCall(id="1", name="double", arguments={"value": 2})]),
                LLMResponse(content="done"),
            ]
        ),
        tools=registry,
        status_sink=sink,
    )

    assert agent.run("go") == "done"

    pairs = {(event.type, event.phase, event.name) for event in sink.events}
    assert ("agent", "start", "agent") in pairs
    assert ("llm", "start", "chat") in pairs
    assert ("llm", "end", "chat") in pairs
    assert ("tool", "start", "double") in pairs
    assert ("tool", "end", "double") in pairs
    assert ("agent", "end", "agent") in pairs


def test_status_events_include_error():
    sink = ListStatusSink()
    agent = Agent(llm=FakeLLM([RuntimeError("boom")]), status_sink=sink)

    try:
        agent.run("go")
    except Exception:
        pass

    assert any(event.type == "error" for event in sink.events)
