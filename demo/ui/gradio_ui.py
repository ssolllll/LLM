import gradio as gr
from mcp_client import ask_mcp
import logging

logging.basicConfig(level=logging.DEBUG)

def chat_fn(message, history):
    history = history or []
    history.append((message, ""))
    bot_reply = ""
    for tok in ask_mcp(message):
        bot_reply += tok
        yield history[:-1] + [(message, bot_reply)], ""
    history[-1] = (message, bot_reply)
    yield history, ""

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    txt = gr.Textbox(show_label=False, placeholder="메세지를 입력하고 Enter")
    txt.submit(
        chat_fn,
        inputs = [txt, chatbot],
        outputs = [chatbot, txt],
    )

demo.launch(server_name='0.0.0.0', server_port=7860)