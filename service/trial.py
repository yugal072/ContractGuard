from mcp.server import MCPServer
from mcp.server.sse import SseServerTransport
from mcp import Client
from mcp.types import TextContent
import asyncio
from typing import Optional, TypedDict
from datetime import datetime

mcp = MCPServer(name="contractguard")


class ServerStatus(TypedDict):
    status: str
    service: list[str]
    message: Optional[str]
    timestamp: Optional[str]

@mcp.tool(title="Get API service health status")
async def get_server_status(endpoint:str, timeout: Optional[int]=None) -> ServerStatus:
    """Get the status of the APi server"""
    return {
        "status": "healthy",
        "service": ["contractguard"],
        "message": f"The server {endpoint} is running fine with the timeout {timeout}",
        "timestamp": datetime.utcnow().isoformat() + "Z", # You can add more fields
    }

async def list_tools():
    async with Client(mcp) as client:
        result = await client.list_tools()
        for tool in result.tools:
            print("Tool Name: ", tool.name)
            print("Tool Title: " , tool.title)
            print("Description: ", tool.description)
            print("Tool input schema: ", tool.input_schema)

async def call_tools():
    async with Client(mcp) as client:
        result = await client.call_tool("get_server_status", {"endpoint": "postman/order", "timeout": 234})
        for block in result.content:
            if isinstance(block, TextContent):
                print(block.text)
        print("Unstructured content: ", result.content)
        print("Structured content: ", result.structured_content)
        print("Errors:  ", result.is_error)



if __name__ == "__main__":
    # Choose ONE of the two lines below depending on the mode you want
    mcp.run(transport='stdio')                                          # stdio  (for OpenCode local)
    #mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)  # HTTP