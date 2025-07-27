import gradio as gr
import ollama

def ollama_chat_interface(message, history):
    messages_for_ollama = []
    for human, ai in history:
        if human:
            messages_for_ollama.append({"role" : "user","content" : human})
        if ai:
            messages_for_ollama.append({"role" : "assistant","content" : ai})
    
    messages_for_ollama.append({"role":"user","content":message})
    response = ollama.chat(
        model='qwen3',
        messages = messages_for_ollama,
        stream=False
    )
    return response['message']['content']

gr.ChatInterface(
    fn=ollama_chat_interface,
    title="Ollama Chatbot with Gradio",
    chatbot=gr.Chatbot(height=400),
    textbox=gr.Textbox(placeholder="메세지를 입력하세요...", container=False, scale=7),
    submit_btn ="전송",
    stop_btn="중지"
).launch()