import gradio as gr
from mcp_client import ask_mcp
import logging

logging.basicConfig(level=logging.DEBUG)

def chat_fn(message, history):
    history = history or []
    history.append((message, ""))
    bot_reply = ""

    try:
        response_generator = ask_mcp(message)
        for tok in ask_mcp(message):
            bot_reply += tok
            yield history[:-1] + [(message, bot_reply)], ""
    
        history[-1] = (message, bot_reply)
        yield history, ""
    except Exception as e:
        history[-1] = (message, f"Error: {str(e)}")
        yield history, ""

def clear_chat():
    return [], ""


with gr.Blocks() as demo:
    gr.Markdown("MCP 통합 AI 어시스턴트")
    chatbot = gr.Chatbot()
    txt = gr.Textbox(show_label=False, placeholder="메세지를 입력하고 Enter")
    clear_btn = gr.Button("초기화", sacle=1, variant="secondary")

    txt.submit(
        chat_fn,
        inputs = [txt, chatbot],
        outputs = [chatbot, txt],
    )
    clear_btn.click(
        clear_chat,
        outputs=[chatbot, txt],
        queue=False
    )

demo.launch(server_name='0.0.0.0', server_port=7860)