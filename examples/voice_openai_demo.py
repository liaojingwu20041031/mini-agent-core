"""VoicePipeline demo from the remote profile with dummy text audio adapters."""

from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.config.loader import load_profile_config
from mini_agent.models.factory import build_agent_from_profile
from mini_agent.voice.audio_input import TextAudioInput
from mini_agent.voice.audio_output import TextAudioOutput
from mini_agent.voice.pipeline import VoicePipeline


def main() -> None:
    config = load_profile_config("config", "remote")
    agent = build_agent_from_profile(config)
    pipeline = VoicePipeline(
        audio_input=TextAudioInput(lambda: input("say> ")),
        stt_engine=DummySTT(),
        agent=agent,
        tts_engine=DummyTTS(),
        audio_output=TextAudioOutput(),
    )
    while True:
        command = input("Enter to push-to-talk, /exit to quit> ").strip()
        if command == "/exit":
            break
        pipeline.run_once()


if __name__ == "__main__":
    main()
