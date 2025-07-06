import os
import json
import httpx
import sseclient
from dotenv import load_dotenv

load_dotenv()

GATEWAY = os.getenv("GATEWAY_URL")

def ask_mcp(prompt: str):
    headers = {"Accept":"text/event-stream"}
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
