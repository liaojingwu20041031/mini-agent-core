from mini_agent.core.tools import ToolRegistry, tool


def test_tool_schema_from_signature():
    @tool(description="Demo tool")
    def demo(name: str, count: int, enabled: bool = True):
        return None

    registry = ToolRegistry()
    definition = registry.register(demo)

    assert definition.name == "demo"
    assert definition.description == "Demo tool"
    assert definition.parameters["properties"]["name"]["type"] == "string"
    assert definition.parameters["properties"]["count"]["type"] == "integer"
    assert definition.parameters["properties"]["enabled"]["type"] == "boolean"
    assert definition.parameters["required"] == ["name", "count"]


def test_openai_tool_schema_shape():
    @tool(name="hello", description="Say hello")
    def greet(name: str):
        return f"hello {name}"

    registry = ToolRegistry()
    registry.register(greet)

    schema = registry.schemas()[0]
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "hello"
    assert schema["function"]["parameters"]["type"] == "object"

