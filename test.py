import streamlit as st
import time
# Import hàm stream bạn vừa thêm vào rag_core.py
from rag_core import generate_corag_stream

# Cấu hình trang Streamlit cho rộng rãi
st.set_page_config(page_title="coRAG - AI Reasoning", layout="wide")

st.title("🧠 Hệ thống coRAG (Reasoning RAG)")
st.markdown("Hệ thống sẽ hiển thị quá trình suy nghĩ trước khi đưa ra câu trả lời cuối cùng.")

# Khởi tạo session_id (Trong thực tế bạn có thể random hoặc lấy từ user login)
if "session_id" not in st.session_state:
    st.session_state.session_id = "test_session_123"

# Ô nhập liệu cho người dùng
user_question = st.chat_input("Nhập câu hỏi của bạn về tài liệu...")

if user_question:
    # Hiển thị câu hỏi của user
    st.chat_message("user").markdown(user_question)

    # Chia layout thành 2 cột: Tỉ lệ 1:1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤔 Quá trình suy nghĩ")
        # Khung chứa text có viền xám nhẹ để phân biệt
        with st.container(border=True):
            think_placeholder = st.empty()
            
    with col2:
        st.markdown("### 💡 Câu trả lời")
        with st.container(border=True):
            answer_placeholder = st.empty()

    # Bắt đầu gọi model và xử lý stream
    full_text = ""
    think_text = ""
    answer_text = ""
    
    # Hàm stream trả về một generator
    try:
        # Chú ý: Cần đảm bảo tài liệu đã được vector hóa và lưu vào đúng session_id này trước đó
        stream_generator = generate_corag_stream(
            user_input=user_question, 
            session_id=st.session_state.session_id
        )
        
        for chunk in stream_generator:
            full_text += chunk
            
            # --- LOGIC BÓC TÁCH STREAM REAL-TIME ---
            if "<think>" in full_text and "</think>" not in full_text:
                # Đang trong giai đoạn suy nghĩ
                think_text = full_text.split("<think>")[1]
                # Thêm icon nhấp nháy tạo cảm giác AI đang gõ
                think_placeholder.markdown(f"*{think_text}* ▌")
                
            elif "</think>" in full_text:
                # Đã nghĩ xong, chốt lại text bên cột trái (bỏ icon nhấp nháy)
                think_text_final = full_text.split("<think>")[1].split("</think>")[0]
                think_placeholder.markdown(f"*{think_text_final}*")
                
                # Kiểm tra xem đã bắt đầu viết answer chưa
                if "<answer>" in full_text and "</answer>" not in full_text:
                    answer_text = full_text.split("<answer>")[1]
                    answer_placeholder.markdown(answer_text + " ▌")
                    
                elif "</answer>" in full_text:
                    # Đã hoàn thành câu trả lời
                    final_answer = full_text.split("<answer>")[1].split("</answer>")[0]
                    answer_placeholder.markdown(final_answer)
                    
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}\nVui lòng kiểm tra lại đường dẫn VectorDB hoặc LLM.")