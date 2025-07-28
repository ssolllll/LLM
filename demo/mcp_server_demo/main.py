from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# 서버 생성 (이름 필수)
mcp = FastMCP(
    # name="Calculator Server",
    # transport="aaaa",     # ★ HTTP(SSE) 모드
    # host="0.0.0.0",      # 외부 바인딩
    port=6276           # 원하는 포트
    # prefix="",           # /invoke, /health 로 단순화 (선택)
    # omit_auth=True,      # 개발 중엔 인증 생략
)

class Operands(BaseModel):
    a: float
    b: float

@mcp.tool()
def add(params: Operands) -> float:
    """Add two numbers"""
    return params.a + params.b

@mcp.tool()
def subtract(params: Operands) -> float:
    """Subtract two numbers"""
    return params.a - params.b

@mcp.tool()
def multiply(params: Operands) -> float:
    """Multiply two numbers"""
    return params.a * params.b

@mcp.tool()
def divide(params: Operands) -> float:
    """Divide two numbers"""
    if params.b == 0:
        raise ValueError("0으로 나눌 수 없습니다.")
    return params.a / params.b

if __name__ == "__main__":
    mcp.run(transport="sse")