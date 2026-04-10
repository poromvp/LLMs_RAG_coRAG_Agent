import streamlit as st
import database as db 
import rag_core as rc
import os
import shutil
st.set_page_config(page_title="Chat2", page_icon="🤖", layout="wide")


# SIDEBAR
# hướng dẫn sử dụng
# tạo mới hoặc hiển thị lịch sử các cuộc trò chuyện
# cài đặt mô hình (điều chỉnh chunk size, chunk_overlap, có so sánh và báo cáo kết quả về độ chính xác, cho phép tuỳ chỉnh các chunk parameters)
# setting (có nút xoá tất cả lịch sử, )
# --- 0. KHỞI TẠO DỮ LIỆU VÀO SESSION STATE ---
# Việc này đảm bảo khi bạn xóa, dữ liệu sẽ được lưu lại trạng thái
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        "Chat 1: Câu 8 của Kiệt", 
        "Chat 2: Tổng quan NCKH", 
        "Chat 3: Đạo đức khoa học"
    ]
if "current_chat" not in st.session_state:
    # Mặc định chọn chat đầu tiên nếu có
    st.session_state.current_chat = st.session_state.chat_history[0] if st.session_state.chat_history else None


def create_side_bar():
    with st.sidebar:
        # 1. TẠO MỚI TRÒ CHUYỆN (Nút nổi bật)
        if st.button("➕ Đoạn chat mới", type="primary", use_container_width=True):
            new_id = db.create_session("Chat mới")
            st.session_state.current_session = new_id
            st.rerun()
        
        st.divider() # Đường gạch ngang phân cách
        
        # 2. LỊCH SỬ CÁC CUỘC TRÒ CHUYỆN
        st.write("🕒 **Lịch sử các cuộc trò truyện**")
        
        sessions = db.get_all_sessions()
        
        # SỬA LỖI Ở ĐÂY: Nếu database rỗng (người dùng mới hoàn toàn)
        if not sessions:
            new_id = db.create_session("Chat mới")
            sessions = [(new_id, "Chat mới")]
            st.session_state.current_session = new_id
        # Còn nếu đã có session nhưng ứng dụng vừa mới load
        elif 'current_session' not in st.session_state:
            st.session_state.current_session = sessions[0][0]

        for sess_id, sess_name in sessions:
            col1, col2 = st.columns([4, 1])
            with col1:
            # Nếu bấm vào tên chat -> Đổi phiên chat hiện tại
                if st.button(sess_name, key=f"btn_{sess_id}", use_container_width=True):
                    st.session_state.current_session = sess_id
                    st.rerun()
            with col2:
            # Nếu bấm nút Xóa -> Xóa DB và xóa luôn thư mục tài liệu của phiên đó
                if st.button("🗑️", key=f"del_{sess_id}"): # [cite: 599]
                    db.delete_session(sess_id)
                    folder_path = f"faiss_data/{sess_id}"
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path) # Xóa sạch rác trong ổ cứng
                    if st.session_state.get('current_session') == sess_id:
                        st.session_state.pop('current_session')
                    st.rerun()
        
        st.divider() # Đường gạch ngang phân cách
        
        # 3. HƯỚNG DẪN SỬ DỤNG
        with st.expander("💡 Hướng dẫn sử dụng"):
            st.markdown("""
            - **Bước 1:** Tải hoặc chọn tài liệu ở panel bên phải.
            - **Bước 2:** Cấu hình tham số Model ở bên dưới nếu cần.
            - **Bước 3:** Đặt câu hỏi liên quan đến tài liệu.
            - **Lưu ý:** Bật chế độ "Báo cáo độ chính xác" để xem hệ thống trích xuất từ đoạn văn nào.
            """)
            
        # 4. CÀI ĐẶT MÔ HÌNH (RAG & Chunking Parameters)
        with st.expander("⚙️ Cài đặt Model & Chunking", expanded=True):
            st.slider("Chunk Size", 100, 1000, 200, help="Kích thước tối đa của mỗi đoạn văn bản được cắt ra.")
            st.slider("Chunk Overlap", 0, 200, 20, help="Số lượng ký tự/token trùng lặp giữa các đoạn để giữ mạch ngữ cảnh.")
            
            st.selectbox("Phương pháp cắt (Splitter)", ["Recursive Character", "Token Splitter", "Sentence Splitter"])
            
            st.write("---") 
            
            st.toggle("📊 Báo cáo & So sánh độ chính xác", value=False, 
                      help="Hệ thống sẽ hiển thị điểm tương đồng (Similarity Score) của các chunk và so sánh kết quả.")

        st.divider()

        # 5. SETTING CHUNG (Khu vực nguy hiểm - Xóa dữ liệu)
        with st.expander("⚙️ Cài đặt hệ thống", expanded=True):
            if st.button("🗑️ Xóa tất cả lịch sử", use_container_width=True):
                st.session_state.chat_history.clear()
                st.session_state.current_chat = None
                st.rerun()
if "viewing_doc" not in st.session_state:
    st.session_state.viewing_doc = None


# MAIN AREA
# hiển thị lịch sử các cuộc trò chuyện , nếu là cuộc trò chuyện mới thì chào mừng
# cho phép nhập câu hỏi và đính kèm nhiều tài liệu cùng lúc
# hiển thị câu trả lời của trợ lý
# hiển thị báo cáo kết quả về độ chính xác
# hiển thị tiến trình xử lý
col_main, col_right = st.columns([3, 1.5], gap="large")
def create_main_area():
    session_id = st.session_state.current_session
    messages = db.get_messages(session_id)
    
    with col_main:
        with st.container(height=500, border=False):
            st.title("Trợ lý ảo RAG Agent 💬")
            
            # Hiển thị lời chào nếu là thư mục mới
            if not messages:
                st.info("👋 Chào mừng bạn đến với RAG Agent! Hãy tải tài liệu lển (🗂️) và đặt câu hỏi để bắt đầu.")
                
            # Render lịch sử trò chuyện từ DB
            for role, content in messages:
                with st.chat_message(role):
                    st.write(content)
                    
    # Lấy input mới (bao gồm cả chữ và file đính kèm)
    user_input_data = st.chat_input("Nhập câu hỏi và đính kèm tài liệu tại đây...", accept_file="multiple")

    if user_input_data:
        text = ""
        uploaded_files = []
        
        # Bóc tách text và file từ Streamlit phiên bản mới (ChatInputValue)
        if hasattr(user_input_data, "text") or hasattr(user_input_data, "files"):
            text = getattr(user_input_data, "text", "") or ""
            uploaded_files = getattr(user_input_data, "files", []) or []
        elif isinstance(user_input_data, dict):
            text = user_input_data.get("text", "") or ""
            uploaded_files = user_input_data.get("files", []) or []
        else:
            # Fallback nếu nó trả về string
            text = str(user_input_data)
            
        # 1. NẾU CÓ FILE -> Đẩy xuống thư mục tạm, chạy DirectoryLoader + Unstructured -> Thêm vào Vector DB
        if uploaded_files:
            temp_dir = f"temp_uploads/{session_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            for f in uploaded_files:
                file_path = os.path.join(temp_dir, f.name)
                # Lưu file tạm xuống ổ cứng
                with open(file_path, "wb") as out_file:
                    out_file.write(f.read())
                # Lưu tracking vào database
                file_type = f.name.split('.')[-1] if '.' in f.name else "unknown"
                db.save_document_metadata(session_id, f.name, file_type)
            
            # Đưa qua rag_core quét, add_documents và lưu FAISS
            with st.spinner(f"🔄 Đang phân tích {len(uploaded_files)} tài liệu. Vui lòng đợi..."):
                rc.process_and_save_documents(temp_dir, session_id)
            
            # Xóa rác thư mục tạm
            shutil.rmtree(temp_dir, ignore_errors=True)
            st.toast("✅ Tài liệu đã được ghi nhớ thành công!", icon="🧠")
            
        # 2. NẾU CÓ CÂU HỎI TEXT -> Lưu DB, chạy LLM -> Lưu DB trả lời -> Vẽ lại
        if text:
            # Hiện text của người dùng
            db.save_message(session_id, "user", text)
            
            with st.spinner("🤖 Trợ lý đang suy nghĩ..."):
                try:
                    # Rút trích danh sách file được người dùng tick ở bên phải:
                    session_docs = db.get_session_documents(session_id)
                    selected_files_to_search = []
                    for doc in session_docs:
                        f_name = doc[1]
                        # Mặc định là True nếu nút checkall/trạng thái cũ là True
                        if st.session_state.get(f"chk_{f_name}", True):
                            selected_files_to_search.append(f_name)

                    # Gửi xuống RAG Chain để truy xuất FAISS và sinh câu trả lời
                    answer = rc.generate_answer(text, session_id, selected_files=selected_files_to_search)
                except Exception as e:
                    answer = f"Lỗi (Có thể bạn chưa upload tài liệu nào để AI trích xuất): {str(e)}"
                    
            db.save_message(session_id, "assistant", answer)
            
        # Cập nhật lại UI sau khi xử lý xong
        st.rerun()

# RIGHT SIDEBAR
# hiển thị tài liệu đã tải lên, cho phép xem tài liệu đó khi nhấn vào, có thể xoá tài liệu
def create_right_side_bar():
    session_id = st.session_state.current_session
    documents = db.get_session_documents(session_id)

    with col_right:
    # TẠO THANH CUỘN ĐỘC LẬP CHO CỘT PHẢI (Cao 700px, có viền)
        with st.container(height=500, border=True):
            
            # TRẠNG THÁI 1: NẾU ĐANG CHỌN XEM MỘT TÀI LIỆU
            if st.session_state.get("viewing_doc") is not None:
                # Dòng tiêu đề có nút Back (Nguồn)
                c_back, c_title = st.columns([0.4, 0.6])
                with c_back:
                    if st.button("↖ Nguồn", help="Quay lại danh sách"):
                        st.session_state.viewing_doc = None
                        st.rerun() 
            
                st.subheader(st.session_state.viewing_doc)
            
                with st.expander("✨ Hướng dẫn về nguồn", expanded=True):
                    st.markdown("""
                    Tính năng tạo tóm tắt file này sẽ được tích hợp bằng AI trong tương lai.
                """)
            
                st.write("Dữ liệu gốc (Văn bản chắt lọc từ tài liệu PDF...).")
            
            # TRẠNG THÁI 2: TRƯỜNG HỢP HIỂN THỊ DANH SÁCH FILE 
            else:
                c_title, c_check = st.columns([0.8, 0.2], vertical_alignment="center")
                with c_title:
                    st.write("**Nguồn tài liệu**")
                
                # Checkbox chọn tất cả
                with c_check:
                    st.checkbox("All", value=True, key="check_all", label_visibility="collapsed")
            
                st.divider()
            
                if not documents:
                    st.info("Chưa có tài liệu nào trong phiên chat này. Hãy upload ở thanh Chat.")
                else:
                    # Hiển thị danh sách file từ Database
                    for doc in documents:
                        doc_id, f_name, f_type, up_at = doc
                        c1, c2 = st.columns([0.85, 0.15], gap="small", vertical_alignment="center")
                    
                        with c1:
                            icon = "📄" if f_type.lower() == "pdf" else ("📘" if f_type.lower() == "docx" else "📝")
                            if st.button(f"{icon} {f_name}", key=f"btn_doc_{doc_id}", use_container_width=True):
                                st.session_state.viewing_doc = f_name
                                st.rerun()
                    
                        with c2:
                            # State checkbox sẽ tự liên kết với tính năng Query của FAISS
                            st.checkbox(f"Chọn {doc_id}", value=st.session_state.get("check_all", True), key=f"chk_{f_name}", label_visibility="collapsed")

        
if __name__ == "__main__":
    create_side_bar()
    create_main_area()
    create_right_side_bar()