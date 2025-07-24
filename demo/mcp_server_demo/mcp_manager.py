import json
import asyncio
from typing import Any, Dict

from langchain_mcp_adapters.client import MultiServerMCPClient
"""
"weather" : {
    "command" : "python",
    "args" : ["./mcp_server/mcp_server_weather.py"],
    "transport" : "stdio"
}
"""

DEFAULT_MCP_CONFIG = {
    "mcpServers" : {}
}

def load_mcp_config() -> Dict[str, Any]:
    try:
        with open("mcp_config.json", "r", encoding='utf-8') as f:
            config = json.load(f)
        return config["mcpServers"]
    except Exception as e:
        return DEFAULT_MCP_CONFIG
    
async def cleanup_mcp_client(client=None):
    if client is not None:
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error occurred while cleaning up MCP client : {str(e)}")

async def initialize_mcp_client():
    mcp_config = load_mcp_config()
    print(f"mcp_config : {mcp_config}")

    try:
        client = MultiServerMCPClient(mcp_config)
        all_tools = await client.get_tools()
        print(f"all tools : {all_tools}")
        return client, all_tools
    
    except Exception as e:
        print(f"Error occurred while initializing MCP client: {str(e)}")
        if "client" in locals():
            await cleanup_mcp_client(client)
        raise