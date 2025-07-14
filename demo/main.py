import time

import uvicorn

from gateway import app

def run_mcp_gateway():
    uvicorn.run(
        "gateway.mcp_gateway:app",
        host = "0.0.0.0",
        port = 6270,
        reload=False,
        log_level="info"
    )

def run_mcp_server():
    from mcp_server_demo.main import mcp
    mcp.run(transport="sse")

def run_gradio_ui():
    from ui.gradio_ui import demo
    demo.launch(server_name="0.0.0.0", server_port=7860)

def main():
    import threading
    gateway_thread = threading.Thread(target=run_mcp_gateway, daemon=True)
    gateway_thread.start()

    time.sleep(1)

    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    time.sleep(3)

    run_gradio_ui()

if __name__ == "__main__":
    main()