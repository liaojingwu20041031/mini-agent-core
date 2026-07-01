from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.core.agent import Agent
from mini_agent.core.llm import LLMResponse
from mini_agent.voice.audio_output import TextAudioOutput
from mini_agent.voice.pipeline import VoicePipeline


class StaticAudioInput:
    def capture(self):
        return b"hello"


class EchoLLM:
    def __init__(self):
        self.seen_messages = None

    def chat(self, messages, tools=None, timeout=None):
        self.seen_messages = messages
        user = next(message.content for message in reversed(messages) if message.role == "user")
        return LLMResponse(content=f"echo {user}")


def test_dummy_voice_pipeline_runs_through_same_agent_core():
    llm = EchoLLM()
    agent = Agent(llm=llm)
    tts = DummyTTS()
    output = TextAudioOutput()
    pipeline = VoicePipeline(
        audio_input=StaticAudioInput(),
        stt_engine=DummySTT(),
        agent=agent,
        tts_engine=tts,
        audio_output=output,
    )

    result = pipeline.run_once()

    assert result.user_text == "hello"
    assert result.agent_text == "echo hello"
    assert tts.last_text == "echo hello"
    assert output.last_audio == b"echo hello"
    assert pipeline.agent is agent
    assert pipeline.stt is pipeline.stt_engine
    assert pipeline.tts is pipeline.tts_engine
    assert any(message.role == "user" and message.content == "hello" for message in agent.session.messages)

