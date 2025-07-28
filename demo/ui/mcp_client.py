import os
import json
import httpx
import sseclient
from dotenv import load_dotenv

load_dotenv()

GATEWAY = os.getenv("GATEWAY_URL")

def ask_mcp(prompt: str):
    headers = {"Accept":"text/event-stream"}

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

class MCPClient:
    def __init__(self):
        self.tools_cache = None
        self.tools_loaded = False

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        if self.tools_cache is not None:
            return self.tools_cache
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{MCP_SERVER_URL}/tools")
                response.raise_for_status()
                self.tools_cache = response.json()
                self.tools_loaded = True
                return self.tools_cache
        except Exception as e:
            return []
        
    async def call_tool(self, tool_name: str, arguments: Dict[str,Any])-> Dict[str,Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "name" : tool_name,
                    "arguments" : arguments
                }
                response = await client.post(f"{MCP_SERVER_URL}/call", json=payload)
                response.raise_for_status()
                return response.json()
            
        except Exception as e:
            return {"error" : str(e)}


def ask_mcp(prompt: str):
    headers = {"Accept":"text/event-stream"}
    ENDPOINT = GATEWAY.rstrip("/")
    with httpx.stream(
        "POST",
        GATEWAY,
        json={"input": prompt},
        headers=headers,
        timeout=None
    ) as response:
        response.raise_for_status()
        buffer = ""
        for chunk in response.iter_raw():
            text = chunk.decode("utf-8", errors='replace')
            buffer += text
            while "\n" in buffer:
                line, buffer = buffer.split("\n",1)
                if not line.strip():
                    continue
                if line.startswith("data:"):
                    payload = line[len("data:"):].strip()
                    try:
                        obj = json.loads(payload)
                        if "content" in obj:
                            yield obj["content"]
                    except json.JSONDecodeError:
                        pass
                elif line.startswith("event:"):
                    evt = line[len("event:"):].strip()
                    if evt == "done":
                        return 
        for raw_line in response.iter_lines():
            if isinstance(raw_line, bytes):
                line = raw_line.decode("utf-8", errors="replace").strip()
            else:
                line = raw_line.strip()

            if not line:
                continue

            if line.startswith("data: "):
                payload = line[len("data:"):].strip()
                try:
                    obj = json.loads(payload)
                    content = obj.get("content")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    pass
            
            elif line.startswith("event:"):
                evt = line[len("event:"):].strip()
                if evt == "done":
                    return
                
        print("[DEBUG] 스트림 닫힘, ask_mcp 종료")
        return

mcp_client = MCPClient()
