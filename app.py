import streamlit as st
# =======================
st.set_page_config(page_title="RAG Agent Chat", page_icon="🤖", layout="wide")

# =======================
# SIDEBAR
# =======================
if "history" not in st.session_state:
    st.session_state.history = {}  # Lưu dưới dạng {id: {title: ..., messages: [...]}}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None # None nghĩa là đang ở màn hình New Chat
if "temp_messages" not in st.session_state:
    st.session_state.temp_messages = []

st.session_state
# --- SIDEBAR: LỊCH SỬ CUỘC TRÒ CHUYỆN ---
with st.sidebar:
    st.title("💬 Poro Chat")
    if st.button("➕ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.temp_messages = []
        st.rerun()
    
    st.write("---")
    st.subheader("Lịch sử")
    # Hiển thị danh sách các cuộc chat từ history
    for chat_id, chat_data in reversed(st.session_state.history.items()):
        if st.button(chat_data["title"], key=chat_id, use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.divider()

    st.header("💡 Instructions")
    st.markdown("""
    1. **Tải lên tài liệu** của bạn bằng công cụ tải file bên phải.
    2. **Đặt câu hỏi** liên quan đến tài liệu ở ô nhập liệu bên dưới.
    3. **Nhận câu trả lời** từ RAG Agent dựa trên tài liệu đã cung cấp.
    """)
    
    st.divider()
    
    st.header("⚙️ Settings")
    st.info("Trạng thái: Sẵn sàng hoạt động.")
    
    st.header("🤖 Model Configuration")
    st.success("Model: Mặc định")

# =======================
# MAIN AREA
# =======================
st.title("Trợ lý ảo RAG Agent 💬")
st.markdown("Hệ thống hỏi đáp dựa trên tài liệu (RAG), giao diện tương tự ChatGPT / Gemini.")



# =======================
# DỮ LIỆU ĐOẠN CHAT (SESSION STATE)
# =======================
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Thêm câu chào mừng
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Xin chào! Tôi có thể giúp gì cho bạn? Hãy tải lên một tài liệu và đặt câu hỏi nhé!"
    })

# =======================
# HIỂN THỊ LỊCH SỬ CHAT
# =======================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =======================
# Ô NHẬP LƯU CÂU HỎI (CHAT INPUT)
# =======================
if prompt := st.chat_input("Nhập câu hỏi và đính kèm tài liệu tại đây...", accept_file="multiple"):
    
    user_text = prompt.text
    uploaded_files = prompt.files

    # Xác định nội dung hiển thị trong chat
    display_text = user_text if user_text else f"*(Đã gửi {len(uploaded_files)} tài liệu đính kèm)*"

    # 1. Thêm câu hỏi của user vào danh sách và hiển thị giao diện
    st.session_state.messages.append({"role": "user", "content": display_text})
    with st.chat_message("user"):
        st.markdown(display_text)
        if uploaded_files:
            for file in uploaded_files:
                st.caption(f"📎 Đính kèm: {file.name}")

    # 2. Xử lý câu trả lời (Hiện tại dùng nội dung giả lập - mock response)
    with st.chat_message("assistant"):
        doc_msg = f" cùng với {len(uploaded_files)} tệp bạn vừa gửi." if uploaded_files else "."
        response = f"Đây là câu trả lời mô phỏng cho câu hỏi: **{user_text}**{doc_msg}"
        st.markdown(response)
    
    # 3. Lưu câu trả lời của Trợ lý vào danh sách
    st.session_state.messages.append({"role": "assistant", "content": response})