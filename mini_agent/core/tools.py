"""Tool decorator, registry, JSON Schema generation, and guarded execution."""

from __future__ import annotations

import inspect
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Any, Callable, get_args, get_origin

from mini_agent.core.guard import ToolGuard
from mini_agent.core.messages import ToolCall, ToolResult
from mini_agent.core.trace import get_logger


RiskLevel = str


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable[..., Any]
    risk_level: RiskLevel = "safe"
    parameters: dict[str, Any] = field(default_factory=dict)
    timeout: float | None = None

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _annotation_to_schema(annotation: Any) -> dict[str, Any]:
    if annotation is inspect.Signature.empty:
        return {"type": "string"}
    origin = get_origin(annotation)
    args = get_args(annotation)
    if annotation is str:
        return {"type": "string"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation in (dict, dict[str, Any]) or origin is dict:
        return {"type": "object"}
    if annotation in (list, list[str]) or origin is list:
        item_schema = _annotation_to_schema(args[0]) if args else {"type": "string"}
        return {"type": "array", "items": item_schema}
    if origin is not None and type(None) in args:
        non_none = [arg for arg in args if arg is not type(None)]
        schema = _annotation_to_schema(non_none[0]) if non_none else {"type": "string"}
        schema["nullable"] = True
        return schema
    return {"type": "string"}


def schema_from_signature(func: Callable[..., Any]) -> dict[str, Any]:
    signature = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, parameter in signature.parameters.items():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        properties[name] = _annotation_to_schema(parameter.annotation)
        if parameter.default is inspect.Signature.empty:
            required.append(name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    risk_level: RiskLevel = "safe",
    timeout: float | None = None,
) -> Callable[..., Any]:
    """Decorate a function as an Agent tool."""

    def decorate(target: Callable[..., Any]) -> Callable[..., Any]:
        if risk_level not in {"safe", "confirm", "danger"}:
            raise ValueError("risk_level must be one of: safe, confirm, danger")
        target.__mini_agent_tool__ = ToolDefinition(
            name=name or target.__name__,
            description=description or inspect.getdoc(target) or target.__name__,
            func=target,
            risk_level=risk_level,
            parameters=schema_from_signature(target),
            timeout=timeout,
        )
        return target

    if func is not None:
        return decorate(func)
    return decorate


class ToolRegistry:
    """In-memory registry for function tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self.logger = get_logger()

    def register(self, func: Callable[..., Any] | ToolDefinition) -> ToolDefinition:
        definition = getattr(func, "__mini_agent_tool__", None)
        if isinstance(func, ToolDefinition):
            definition = func
        if not isinstance(definition, ToolDefinition):
            raise TypeError("register expects a @tool-decorated function or ToolDefinition")
        self._tools[definition.name] = definition
        return definition

    def register_many(self, funcs: list[Callable[..., Any]]) -> None:
        for func in funcs:
            self.register(func)

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        return [definition.openai_schema() for definition in self.list()]

    def execute(
        self,
        call: ToolCall,
        guard: ToolGuard | None = None,
        default_timeout: float = 30,
    ) -> ToolResult:
        definition = self.get(call.name)
        if definition is None:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                is_error=True,
                error=f"Unknown tool: {call.name}",
            )

        active_guard = guard or ToolGuard()
        allowed, reason = active_guard.check(definition.name, definition.risk_level, call.arguments)
        if not allowed:
            self.logger.warning("tool blocked name=%s reason=%s", definition.name, reason)
            return ToolResult(
                tool_call_id=call.id,
                name=definition.name,
                is_error=True,
                error=reason,
            )

        timeout = definition.timeout or default_timeout
        self.logger.info("tool start name=%s risk=%s args=%s", definition.name, definition.risk_level, call.arguments)
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(definition.func, **call.arguments)
            content = future.result(timeout=timeout)
        except FutureTimeoutError:
            error = f"Tool timed out after {timeout} seconds."
            self.logger.error("tool timeout name=%s timeout=%s", definition.name, timeout)
            return ToolResult(call.id, definition.name, is_error=True, error=error)
        except Exception as exc:
            self.logger.error("tool error name=%s error=%s", definition.name, exc)
            return ToolResult(
                call.id,
                definition.name,
                is_error=True,
                error=f"{type(exc).__name__}: {exc}",
                content={"traceback": traceback.format_exc(limit=3)},
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        self.logger.info("tool end name=%s", definition.name)
        return ToolResult(call.id, definition.name, content=content)


