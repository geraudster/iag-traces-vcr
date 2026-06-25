import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def dump_mcp_schemas(server_command: str, server_args: list[str], output_file: str = "mcp_tools_schema.json"):
    print(f"Connecting to real MCP server: {server_command} {' '.join(server_args)}")
    
    server_params = StdioServerParameters(
        command=server_command,
        args=server_args,
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Fetch the original tools list
            tools_response = await session.list_tools()
            
            # Convert the tools to dictionaries for JSON serialization
            tools_data = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_response.tools
            ]
            
            with open(output_file, 'w') as f:
                json.dump(tools_data, f, indent=2)
                
            print(f"Successfully dumped {len(tools_data)} tool schemas to {output_file}")

if __name__ == "__main__":
    # Replace with the command you use to start your REAL MCP server
    # e.g., ["python", "my_real_server.py"] or ["npx", "-y", "@modelcontextprotocol/server-postgres", ...]
    asyncio.run(dump_mcp_schemas("python", ["my_real_server.py"]))
