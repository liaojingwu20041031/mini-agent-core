from mini_agent.core.messages import Message
from mini_agent.core.session import Session


def test_session_keeps_system_prompt_and_resets_history():
    session = Session(system_prompt="system")
    session.add(Message(role="user", content="hello"))
    assert [message.role for message in session.messages] == ["system", "user"]

    session.reset()
    assert len(session.messages) == 1
    assert session.messages[0].role == "system"
    assert session.messages[0].content == "system"

