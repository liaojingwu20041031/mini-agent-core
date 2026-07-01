"""Sketch for exposing an edge device operation as an HTTP-backed tool."""

from mini_agent.core.tools import tool


@tool(description="Send a mock command to an edge runtime over HTTP.", risk_level="confirm")
def edge_set_led(state: str) -> dict:
    return {"edge_runtime": "not_connected", "requested_led": state}

