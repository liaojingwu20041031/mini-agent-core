"""VoicePipeline demo with configured OpenAI-compatible Agent and dummy audio adapters."""

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.builtin_tools import register_builtin_tools
from mini_agent.core.agent import Agent
from mini_agent.core.config import load_config, parse_extra_body
from mini_agent.core.guard import ToolGuard
from mini_agent.core.tools import ToolRegistry
from mini_agent.voice.audio_input import TextAudioInput
from mini_agent.voice.audio_output import TextAudioOutput
from mini_agent.voice.pipeline import VoicePipeline


def confirm(name: str, arguments: dict) -> bool:
    answer = input(f"Confirm tool {name} with {arguments}? [y/N] ").strip().lower()
    return answer == "y"


def main() -> None:
    config = load_config()
    registry = ToolRegistry()
    register_builtin_tools(registry)
    llm = OpenAICompatibleClient.from_provider(
        provider=config.llm_provider,
        region=config.llm_region,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model,
        timeout=config.llm_timeout,
        temperature=config.llm_temperature,
        extra_body=parse_extra_body(config),
    )
    agent = Agent(
        llm=llm,
        tools=registry,
        max_steps=config.agent_max_steps,
        llm_timeout=config.llm_timeout,
        guard=ToolGuard(confirm_callback=confirm, allow_danger=config.allow_danger_tools),
    )
    pipeline = VoicePipeline(
        audio_input=TextAudioInput(lambda: input("say> ")),
        stt=DummySTT(),
        agent=agent,
        tts=DummyTTS(),
        audio_output=TextAudioOutput(),
    )
    while True:
        command = input("Enter to push-to-talk, /exit to quit> ").strip()
        if command == "/exit":
            break
        pipeline.run_once()


if __name__ == "__main__":
    main()
