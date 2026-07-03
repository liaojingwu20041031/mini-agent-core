"""Process wrapper placeholder for MCP stdio servers."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from mini_agent.mcp.server_config import MCPServerConfig


@dataclass
class MCPProcess:
    config: MCPServerConfig
    process: subprocess.Popen | None = None

    def start(self) -> None:
        if not self.config.enabled:
            return
        if self.config.transport != "stdio":
            raise ValueError(f"Unsupported MCP transport in V0.1: {self.config.transport}")
        if not self.config.command:
            raise ValueError(f"MCP server {self.config.name} has no command")
        self.process = subprocess.Popen(
            [self.config.command, *self.config.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, **self.config.env},
        )

    def stop(self, timeout: float = 5) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
