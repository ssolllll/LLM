import logging

import gradio as gr

from .mcp_client import ask_mcp
from .session import SessionManager, convert_messages_to_gradio_history, format_session_display

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

session_manager = SessionManager()

def chat_fn(message, history, session_id):
    if not message.strip():
        return history, "", session_id, gr.update()
    
    if not session_id or not session_manager.session_exists(session_id):
        title = message[:30] + "..." if len(message) > 30 else message
        session_id = session_manager.create_session(title)
    
    history = history or []
    history.append((message, ""))
    bot_reply = ""

    try:
        session_manager.add_message(session_id, "user", message)

        response_generator = ask_mcp(message)

        for token in response_generator:
            bot_reply += token

            current_history = history[:-1] + [(message, bot_reply)]
            yield current_history, "", session_id, gr.update()

        history[-1] = (message, bot_reply)
        
        session_manager.add_message(session_id, "assistant", bot_reply)

        sessions = session_manager.get_sessions()
        session_choices = [
            (format_session_display(s), s['session_id'])
            for s in sessions
        ]

        yield history, "", session_id, gr.update(choices=session_choices)

    except Exception as e:
        print(f"[ERROR] Exception in chat_fn: {e}")
        history[-1] = (message, f"Error: {str(e)}")
        yield history, "", session_id, gr.update()

def load_session(selected_session_id):
    if not selected_session_id:
        return [], ""
    
    try:
        if not session_manager.session_exists(selected_session_id):
            return [], ""
        
        messages = session_manager.get_messages(selected_session_id)
        history = convert_messages_to_gradio_history(messages)

        return history, selected_session_id
    except Exception as e:
        logger.error(f"Error loading session {selected_session_id}: {e}")
        return [], ""

def create_new_session():
    try:
        new_session_id = session_manager.create_session("New Session")
        
        sessions = session_manager.get_sessions()
        session_choices = [
            (format_session_display(s), s['session_id'])
            for s in sessions
        ]

        return [], "", new_session_id, gr.update(choices=session_choices, value=new_session_id)

    except Exception as e:
        logger.error(f"Error creating new session: {e}")
        return [], "", "", gr.update()
        
def delete_session(session_id):
    if not session_id:
        return [], "", "", gr.update()
    
    try:
        session_manager.delete_session(session_id)
        
        sessions = session_manager.get_sessions()
        session_choices = [
            (format_session_display(s), s['session_id'])
            for s in sessions
        ]

        return [], "", "", gr.update(choices=session_choices, value=None)

    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return [], "", session_id, gr.update()

def get_initial_session_choices():
    """초기 세션 목록 가져오기"""
    try:
        sessions = session_manager.get_sessions()
        return [
            (format_session_display(s), s['session_id']) 
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"세션 목록 로드 오류: {e}")
        return []

def clear_current_chat():
    """현재 채팅창만 초기화 (DB는 유지)"""
    return [], ""

with gr.Blocks(
    title="MCP AI Assistant", 
    theme=gr.themes.Soft(),
    css="""
    .session-sidebar {
        min-height: 600px;
        border-right: 1px solid #e0e0e0;
    }
    .chat-container {
        min-height: 600px;
    }
    """
) as demo:
    
    # 현재 세션 상태
    current_session_id = gr.State("")
    
    # 제목
    gr.Markdown("# 🤖 MCP AI Assistant")
    
    with gr.Row():
        # 왼쪽 사이드바 - 세션 관리
        with gr.Column(scale=1, elem_classes="session-sidebar"):
            gr.Markdown("### 📋 세션 관리")
            
            # 세션 목록
            session_list = gr.Radio(
                label="세션 선택",
                choices=get_initial_session_choices(),
                value="",
                interactive=True,
                elem_id="session-list"
            )
            
            # 세션 관리 버튼들
            with gr.Row():
                new_btn = gr.Button("🆕 새 세션", size="sm", variant="primary")
                delete_btn = gr.Button("🗑️ 삭제", size="sm", variant="secondary")
            
            # 세션 정보 표시
            gr.Markdown("*세션을 선택하면 이전 대화를 불러옵니다*")
        
        # 오른쪽 채팅 영역
        with gr.Column(scale=3, elem_classes="chat-container"):
            # 채팅봇
            chatbot = gr.Chatbot(
                height=500,
                show_label=False,
                container=True,
                bubble_full_width=False
            )
            
            # 입력 영역
            with gr.Row():
                txt_input = gr.Textbox(
                    show_label=False,
                    placeholder="메시지를 입력하고 Enter를 누르세요...",
                    scale=4,
                    lines=1
                )
                clear_chat_btn = gr.Button("🗑️ 채팅 초기화", scale=1, variant="secondary")

    # 이벤트 핸들러들
    
    # 메시지 전송
    txt_input.submit(
        chat_fn,
        inputs=[txt_input, chatbot, current_session_id],
        outputs=[chatbot, txt_input, current_session_id, session_list],
    )
    
    # 세션 선택
    session_list.change(
        load_session,
        inputs=[session_list],
        outputs=[chatbot, current_session_id]
    )
    
    # 새 세션 생성
    new_btn.click(
        create_new_session,
        outputs=[chatbot, txt_input, current_session_id, session_list]
    )
    
    # 세션 삭제
    delete_btn.click(
        delete_session,
        inputs=[current_session_id],
        outputs=[chatbot, txt_input, current_session_id, session_list]
    )
    
    # 채팅 초기화 (현재 화면만)
    clear_chat_btn.click(
        clear_current_chat,
        outputs=[chatbot, txt_input]
    )

def launch_ui(host="0.0.0.0", port=7860, share=False, debug=False):
    """UI 실행 함수"""
    logger.info("세션 관리 기능이 활성화된 AI Assistant를 시작합니다.")
    logger.info(f"서버 주소: http://{host}:{port}")
    
    demo.launch(
        server_name=host,
        server_port=port,
        share=share,
        debug=debug,
        show_error=True
    )

# 직접 실행시
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)