import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 1. Load the mock trajectory data (Inputs & Outputs)
try:
    with open("mock_trajectory.json", "r") as f:
        MOCK_DATA = json.load(f)
except FileNotFoundError:
    MOCK_DATA = {}

# 2. Load the original tool schemas (Descriptions & JSON Schemas)
try:
    with open("mcp_tools_schema.json", "r") as f:
        SCHEMA_DATA = json.load(f)
except FileNotFoundError:
    print("Error: mcp_tools_schema.json not found. Run dump_schemas.py first.")
    SCHEMA_DATA = []

app = Server("mock-vcr-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Return the exact tools and descriptions exposed by the original server."""
    tools = []
    for tool_dict in SCHEMA_DATA:
        # Optional: Only expose tools that are actually in our mock trajectory
        # If you want to expose ALL original tools, remove this if-statement.
        if tool_dict["name"] in MOCK_DATA:
            tools.append(
                types.Tool(
                    name=tool_dict["name"],
                    description=tool_dict["description"],
                    inputSchema=tool_dict["inputSchema"]
                )
            )
    return tools


def is_fuzzy_match(expected: dict, actual: dict) -> bool:
    """Checks if the actual arguments contain the expected key-value pairs."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return expected == actual

    for key, val in expected.items():
        # Check if actual has the key and if the values match (case-insensitive for strings)
        if key not in actual:
            return False

        actual_val = actual[key]
        if isinstance(val, str) and isinstance(actual_val, str):
            if val.lower() != actual_val.lower():
                return False
        elif val != actual_val:
            return False

    return True

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Intercept tool calls and return mocked data if arguments match."""
    if name not in MOCK_DATA:
        return [types.TextContent(type="text", text=f"Error: Tool '{name}' not found in mock data.")]

    arguments = arguments or {}

    # 1. Try to find a matching tool call in our trajectory
    for call in MOCK_DATA[name]:
        expected_input = call.get("expected_input", {})

        if is_fuzzy_match(expected_input, arguments):
            mock_output = call.get("mocked_output")

            # MCP requires string outputs, so we serialize dicts
            if isinstance(mock_output, (dict, list)):
                text_output = json.dumps(mock_output)
            else:
                text_output = str(mock_output)

            return [types.TextContent(type="text", text=text_output)]

    # 2. Fallback error if the LLM hallucinated entirely different arguments
    expected_list = [c.get('expected_input') for c in MOCK_DATA[name]]
    error_msg = (
        f"VCR Error: No mock found for tool '{name}' with arguments: {arguments}\n"
        f"Expected one of: {json.dumps(expected_list, indent=2)}"
    )
    return [types.TextContent(type="text", text=error_msg)]


import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

# ... [Keep your MOCK_DATA, SCHEMA_DATA, and @app decorators exactly as they are] ...

# 1. Initialize the SSE Transport pointing to a dedicated messages endpoint
sse = SseServerTransport("/messages/")

# 2. Handle the initial SSE connection from the agent
async def handle_sse(request):
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        # Pass the streams to the MCP Server instance you defined earlier
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

# 3. Handle incoming tool execution requests from the agent
async def handle_messages(request):
    await sse.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )

# 4. Map the endpoints to a Starlette application
starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    print("Starting mock MCP VCR server on http://localhost:8000/sse")
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)
