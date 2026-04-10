import sqlite3
import uuid
from datetime import datetime

DB_NAME = "chat_history.db"

def get_connection():
    # check_same_thread=False giúp Streamlit không bị lỗi khi nhiều luồng cùng gọi DB
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    """Khởi tạo database và các bảng nếu chưa có"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng 1: Quản lý các phiên chat (Hiển thị ở Sidebar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at DATETIME
        )
    ''')
    
    # Bảng 2: Quản lý chi tiết từng tin nhắn trong phiên chat (Câu hỏi 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT, -- 'user' hoặc 'assistant'
            content TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    ''')
    
    # Bảng 3: Quản lý File & Metadata cho Multi-document RAG (Câu hỏi 8)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_name TEXT,
            file_type TEXT,
            uploaded_at DATETIME,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# ==========================================
# CÁC HÀM QUẢN LÝ PHIÊN CHAT (SESSIONS)
# ==========================================

def create_session(name="Chat mới"):
    """Tạo một phiên chat mới và trả về ID"""
    conn = get_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    cursor.execute('INSERT INTO sessions (id, name, created_at) VALUES (?, ?, ?)', 
                   (session_id, name, datetime.now()))
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    """Lấy danh sách các phiên chat để vẽ Sidebar"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM sessions ORDER BY created_at DESC')
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def delete_session(session_id):
    """Xóa một phiên chat (xóa luôn cả tin nhắn và tài liệu liên quan nhờ DELETE CASCADE)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON') 
    cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()

# ==========================================
# CÁC HÀM QUẢN LÝ TIN NHẮN (MESSAGES)
# ==========================================

def save_message(session_id, role, content):
    """Lưu một tin nhắn mới vào database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
                   (session_id, role, content))
    conn.commit()
    conn.close()

def get_messages(session_id):
    """Lấy toàn bộ lịch sử chat của một phiên"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC', (session_id,))
    messages = cursor.fetchall()
    conn.close()
    return messages

# ==========================================
# CÁC HÀM QUẢN LÝ TÀI LIỆU (DOCUMENTS) - MỚI
# ==========================================

def save_document_metadata(session_id, file_name, file_type):
    """Lưu thông tin metadata của một file khi người dùng upload"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO documents (session_id, file_name, file_type, uploaded_at) VALUES (?, ?, ?, ?)',
                   (session_id, file_name, file_type, datetime.now()))
    conn.commit()
    conn.close()

def get_session_documents(session_id):
    """Lấy danh sách các file đã upload trong một phiên chat (dùng để làm filter)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, file_name, file_type, uploaded_at FROM documents WHERE session_id = ? ORDER BY uploaded_at DESC', (session_id,))
    documents = cursor.fetchall()
    conn.close()
    return documents