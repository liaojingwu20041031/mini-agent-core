"""Run VoicePipeline without microphone or TTS model."""

from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.core.agent import Agent
from mini_agent.core.llm import LLMResponse
from mini_agent.voice.audio_input import TextAudioInput
from mini_agent.voice.audio_output import TextAudioOutput
from mini_agent.voice.pipeline import VoicePipeline


class EchoLLM:
    def chat(self, messages, tools=None, timeout=None):
        last_user = next(message.content for message in reversed(messages) if message.role == "user")
        return LLMResponse(content=f"echo: {last_user}")


def main() -> None:
    pipeline = VoicePipeline(
        audio_input=TextAudioInput(lambda: input("say> ")),
        stt=DummySTT(),
        agent=Agent(llm=EchoLLM()),
        tts=DummyTTS(),
        audio_output=TextAudioOutput(),
    )
    while True:
        command = input("Enter to talk, /exit to quit> ").strip()
        if command == "/exit":
            break
        pipeline.run_once()


if __name__ == "__main__":
    main()

