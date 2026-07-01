"""Push-to-talk style voice CLI using the configurable VoicePipeline."""

from __future__ import annotations

from mini_agent.voice.pipeline import VoicePipeline


class VoiceCLI:
    def __init__(self, pipeline: VoicePipeline) -> None:
        self.pipeline = pipeline

    def run(self) -> None:
        print("mini-agent voice CLI. Press Enter to push-to-talk, type /exit to quit.")
        while True:
            command = input("push-to-talk> ").strip()
            if command == "/exit":
                break
            self.pipeline.run_once()

