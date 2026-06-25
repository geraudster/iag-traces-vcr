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

# ... [Keep the is_fuzzy_match and @app.call_tool() exactly the same as before] ...

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
