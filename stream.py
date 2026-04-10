import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
        /* Tùy chỉnh vùng Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #202123; /* Màu tối giống ChatGPT */
        }
        
        /* Làm phẳng nút bấm */
        div.stButton > button {
            border: none;
            background-color: transparent;
            text-align: left;
            width: 100%;
            padding: 10px 15px;
            color: #ececf1;
            border-radius: 5px;
        }

        /* Hiệu ứng hover cho hàng */
        div.stButton > button:hover {
            background-color: #2d2d2e;
            color: white;
        }

        /* Làm nổi bật nút đang được chọn */
        div.stButton > button[kind="primary"] {
            background-color: #343541;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

def set_chat_style():
    st.markdown("""
        <style>
            /* Tìm các block tin nhắn của user dựa trên data-testid */
            /* Lưu ý: Cấu trúc CSS có thể thay đổi nhẹ tùy phiên bản Streamlit */
            
            /* Đẩy toàn bộ khung tin nhắn user sang phải */
            .stChatMessage:has([data-testid="stChatMessageAvatarUser"]) {
                flex-direction: row-reverse;
                text-align: right;
                background-color: #202123; /* Có thể đổi màu nền riêng cho User */
                border-radius: 10px;
            }

            /* Điều chỉnh lại nội dung bên trong tin nhắn user */
            .stChatMessage:has([data-testid="stChatMessageAvatarUser"]) .stChatMessageContent {
                text-align: left; /* Để văn bản bên trong vẫn canh trái cho dễ đọc, nhưng là từ ở giữa trở đi */
                
                display: inline-block;
                width: auto;
            }
        </style>
    """, unsafe_allow_html=True)

#set_chat_style()

if "chat_list" not in st.session_state:
    st.session_state.chat_list = ["Chat 1", "Chat 2"]

def change_chat(chat_name):
    # Lưu tên chat đang mở vào tham số URL (ví dụ: localhost:8501/?chat=Chat+1)
    st.query_params["chat"] = chat_name

def side_bar():
    with st.sidebar:
        st.title("💬 Poro Chat")
        # Nút tạo chat mới
        if st.button("New Chat", type="primary", key="new_chat"):
            new_id = len(st.session_state.chat_list) + 1
            new_name = f"Chat {new_id}"
            st.session_state.chat_list.append(new_name)
            # Tự động nhảy sang phòng chat vừa tạo
            st.query_params["chat"] = new_name

        st.divider()
        # Tính toán chiều cao
        dynamic_height = min(len(st.session_state.chat_list) * 50, 400)
        if dynamic_height == 0: dynamic_height = 10 
        
        with st.container(height=dynamic_height, border=False):
            col_chat, col_optional = st.columns([4,1])
            for chat_name in st.session_state.chat_list: 
                with col_chat:
                    # Khi bấm sẽ gọi hàm change_chat để lưu state
                    st.button(chat_name, key=f"chat_{chat_name}", on_click=change_chat, args=(chat_name,))
                with col_optional:
                    with st.popover("⋮", use_container_width=True):
                        st.button("🗑️", key=f"delete_{chat_name}")
                        st.button("✏️", key=f"rename_{chat_name}")
        st.divider()
    

def main_area():
    # Đọc xem URL đang hiển thị phòng chat nào
    current_chat = st.query_params.get("chat", None)
    
    if current_chat:
        st.title(current_chat)
        st.divider()
        st.write("Đang trong màn hình của: ", current_chat)

        # Giả lập tin nhắn
        messages = [
            {"role": "user", "content": "Chào Bot, bạn khỏe không?"},
            {"role": "assistant", "content": "Chào Poro, mình là AI của bạn đây!"}
        ]

        for msg in messages:
            # 'user' sẽ có icon người, 'assistant' sẽ có icon robot
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    else:
        # Nếu không có (lần đầu vào web), hiển thị màn hình chính
        st.title("RAG Agent Chat")
        st.divider()
        st.write("Đây là màn hình mặc định ban đầu.")
    user_input_data = st.chat_input("Nhập câu hỏi và đính kèm tài liệu tại đây...", accept_file="multiple")
    #st.write("Session state hiện tại:")
    #st.write(st.session_state)


def main():
    side_bar()
    main_area() # Gọi hàm vẽ giao diện chính ở đây
    

if __name__ == "__main__":
    main()