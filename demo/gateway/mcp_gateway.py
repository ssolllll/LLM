import os
import json
import httpx
import asyncio
from dotenv import load_dotenv
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.outputs import ChatResult

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("LLM_MODEL")

app = FastAPI(title="MCP Gateway (SSE)")

async def call_ollama(prompt: str):
    payload = {
        "model": MODEL,
        "messages": [{"role":"user","content": prompt}],
    }
    async with httpx.AsyncClient(timeout=None) as cli:
        async with cli.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json=payload,
        ) as resp:
            async for line in resp.aiter_lines():
                # line: 순수 JSON 문자열
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Ollama v3.2 포맷: obj["message"]["content"]
                content = obj.get("message", {}).get("content")
                done_flag = obj.get("done", False)
                if content:
                    yield content
                if done_flag:
                    break

async def call_ollama_with_langchain(prompt: str) -> AsyncGenerator[ChatResult, None]:
    """
    LangChain ChatOllama를 사용하여 Ollama 모델을 호출하고 스트리밍 응답을 생성함.
    """
    ollama = ChatOllama(model=MODEL, base_url = OLLAMA_URL)

    async def stream():
        async for token in ollama.astream(prompt):
            yield token
        
    async for message in stream():
        yield message

@app.post("/invoke/ollama_url")
async def invoke(req: Request):
    prompt = (await req.json()).get("input", "")
    async def event_stream():
        try:
            async for tok in call_ollama(prompt):
                print(tok)
                print(type(tok))
                yield f"data: {json.dumps({'content': tok})}\n\n"
        finally:
            # 스트림 끝내기
            yield "event: done\ndata: {}\n\n"
            await asyncio.sleep(0)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/invoke/langchain")
async def invoke(req: Request):
    prompt = (await req.json()).get("input", "")
    async def event_stream():
        try:
            async for message in call_ollama_with_langchain(prompt):
                content = message.content
                yield f"data: {json.dumps({'content':content})}\n\n"
        finally:
            # 스트림 끝내기
            yield "event: done\ndata: {}\n\n"
            await asyncio.sleep(0)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_gateway:app", host="0.0.0.0", port=6277, reload=True)