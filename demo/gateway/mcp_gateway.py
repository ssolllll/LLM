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

from mcp_server_demo import initialize_mcp_client, load_mcp_config

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

async def call_chatOllama(question: str) -> AsyncGenerator[ChatResult, None]:
    """
    LangChain ChatOllama를 사용하여 Ollama 모델을 호출하고 스트리밍 응답을 생성함.
    """
    _, mcp_tools = await initialize_mcp_client()
    system_prompt = """
    당신은 도움이 되는 AI 어시스턴트입니다.
    도구는 다음 경우에만 사용하세요:
    - 실시간 정보가 필요한 경우
    - 계산이나 파일 작업이 필요한 경우
    - 외부 데이터 검색이 필요한 경우

    인사말, 일반적인 질문, 이미 알고 있는 정보에 대해서는 도구를 사용하지 마세요.
    """

    ollama = ChatOllama(
        model=MODEL,
        base_url = OLLAMA_URL,
        system = system_prompt
    ).bind_tools(mcp_tools)

    final_response = await ollama.invoke(question)

    print(f"Final response: {final_response}")

    if 'messages' in final_response:
        for message in final_response['messages']:
            if hasattr(message, 'content') and message.content:
                if not (hasattr(message, 'type') and message.type == 'human'):
                    yield message.content
    else:
        yield "No response received from agent"

    # async def stream():
    #     async for token in ollama.astream(prompt):
    #         yield token
        
    # async for message in stream():
    #     yield message

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
            async for message in call_chatOllama(prompt):
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