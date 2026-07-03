from mini_agent.core.messages import Message, ToolCall
from mini_agent.core.session import Session


def test_session_keeps_system_prompt_and_resets_history():
    session = Session(system_prompt="system")
    session.add(Message(role="user", content="hello"))
    assert [message.role for message in session.messages] == ["system", "user"]

    session.reset()
    assert len(session.messages) == 1
    assert session.messages[0].role == "system"
    assert session.messages[0].content == "system"


def test_session_trim_keeps_tool_call_pairs_together():
    session = Session(system_prompt="system", max_messages=4)
    session.add(Message(role="user", content="old"))
    session.add(Message(role="assistant", content="old answer"))
    session.add(Message(role="user", content="use tools"))
    session.add(Message(role="assistant", tool_calls=[ToolCall(id="call-1", name="demo")]))
    session.add(Message(role="tool", tool_call_id="call-1", name="demo", content="ok"))

    assert [message.role for message in session.messages] == ["system", "user", "assistant", "tool"]
    assert session.messages[-2].tool_calls[0].id == session.messages[-1].tool_call_id


def test_session_trim_drops_orphan_tool_messages():
    session = Session(max_messages=2)
    session.add(Message(role="tool", tool_call_id="missing", name="demo", content="orphan"))
    session.add(Message(role="user", content="hello"))
    session.add(Message(role="assistant", content="hi"))

    assert [message.role for message in session.messages] == ["user", "assistant"]
