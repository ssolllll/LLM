import uuid
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, db_path: str = "chatbot_sessions.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database and create the sessions table if it doesn't exist."""
        with self.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title TEXT DEFAULT 'New Chat'
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT CHECK(role IN ('user', 'assistant')),
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_messages 
                ON messages(session_id, timestamp)
            """)
        logger.info("Database initialized and tables created")

    @contextmanager
    def get_connection(self):
        """Context manager to handle database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
        finally:
            conn.close()

    def create_session(self, session_id: str, title: str = "New Chat"):
        """Create a new session with the given session_id and title."""
        session_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, title) 
                VALUES (?, ?)
            """, (session_id, title))
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def get_sessions(self, limit: int = 50)-> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT session_id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE session_id = s.session_id) as message_count
                FROM sessions s
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Retrieve session information by session_id."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT session_id, title, created_at, updated_at
                FROM sessions 
                WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        
    def get_messages(self, session_id : str) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT role, content, timestamp
                FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_message(self, session_id: str, role: str, content: str):
        """메시지 추가 (role: 'user' 또는 'assistant')"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            # 세션 업데이트 시간 갱신
            conn.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
    
    def delete_session(self, session_id: str):
        """세션 및 관련 메시지 삭제"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        logger.info(f"세션 삭제: {session_id}")
    
    def update_session_title(self, session_id: str, title: str):
        """세션 제목 업데이트"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (title, session_id)
            )
    
    def session_exists(self, session_id: str) -> bool:
        """세션 존재 여부 확인"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", 
                (session_id,)
            )
            return cursor.fetchone() is not None

def convert_messages_to_gradio_history(messages: List[Dict]) -> List[Tuple[str, str]]:
    """DB 메시지를 Gradio 히스토리 형식으로 변환"""
    history = []
    current_pair = [None, None]
    
    for msg in messages:
        if msg['role'] == 'user':
            if current_pair[0] is not None:
                # 이전 대화 쌍이 완성되지 않았으면 추가
                history.append((current_pair[0], current_pair[1] or ""))
            current_pair = [msg['content'], None]
        elif msg['role'] == 'assistant':
            current_pair[1] = msg['content']
    
    # 마지막 대화 쌍 추가
    if current_pair[0] is not None:
        history.append((current_pair[0], current_pair[1] or ""))
    
    return history

def format_session_display(session: Dict) -> str:
    """세션을 UI 표시용 문자열로 포맷"""
    title = session['title']
    message_count = session.get('message_count', 0)
    updated_at = session['updated_at']
    
    # 시간 포맷 (예: "12/25 14:30")
    try:
        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        time_str = dt.strftime("%m/%d %H:%M")
    except:
        time_str = "Unknown"
    
    return f"{title} ({message_count}msg) - {time_str}"