import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Chat2 - RAG vs coRAG", page_icon="🤖", layout="wide")

# --- 0. KHỞI TẠO DỮ LIỆU VÀO SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        "Chat 1: Câu 8 của Kiệt", 
        "Chat 2: Tổng quan NCKH", 
        "Chat 3: Đạo đức khoa học"
    ]
if "current_chat" not in st.session_state:
    st.session_state.current_chat = st.session_state.chat_history[0] if st.session_state.chat_history else None

if "viewing_doc" not in st.session_state:
    st.session_state.viewing_doc = None

# Dữ liệu giả lập cho tài liệu
danh_sach_tai_lieu = [
    "Chương 1 - Tổng quan.pdf", "Chương 2 - PPNCHK.pdf",
    "Chương 3 - Quy trình NCKH.pdf", "Chương 4 - Đánh giá công trình.pdf",
    "Chương 5 - Đạo đức Khoa học.pdf"
]

# --- 1. HÀM VẼ BIỂU ĐỒ BÁO CÁO (PHƯƠNG ÁN 1) ---
def display_comparison_report():
    st.write("") 
    st.divider()
    st.subheader("📊 Phân tích hiệu năng hệ thống: RAG vs coRAG")
    
    # Giả lập dữ liệu so sánh
    metrics_data = {
        'Chỉ số': ['Thời gian (s)', 'Độ chính xác (%)', 'Độ tin cậy (%)', 'Token (k)'],
        'RAG': [2.1, 72, 65, 0.8],
        'coRAG': [4.5, 94, 98, 1.5]
    }
    df = pd.DataFrame(metrics_data)
    df_melted = df.melt('Chỉ số', var_name='Engine', value_name='Giá trị')

    # Chia layout báo cáo: Trái biểu đồ, Phải các thẻ Metric
    # [6, 1.5] để khớp với tỉ lệ [3+3, 1.5] của phần trên
    col_plot, col_metric = st.columns([6, 1.5], gap="large")

    with col_plot:
        fig = px.bar(df_melted, x='Chỉ số', y='Giá trị', color='Engine', 
                     barmode='group', height=300,
                     color_discrete_map={'RAG': '#1f77b4', 'coRAG': '#ff7f0e'},
                     text_auto='.1f')
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_metric:
        st.metric("Cải thiện chính xác", "+22%", delta="Rất cao")
        st.metric("Độ trễ (Latency)", "4.5s", delta="+2.4s", delta_color="inverse")
        st.caption("⚠️ coRAG chính xác hơn nhưng tốn tài nguyên hơn.")

# --- 2. CÁC HÀM GIAO DIỆN (SIDEBAR & MAIN) ---
def create_side_bar():
    with st.sidebar:
        if st.button("➕ Đoạn chat mới", type="primary", use_container_width=True):
            new_chat_name = f"Chat mới {len(st.session_state.chat_history) + 1}"
            st.session_state.chat_history.insert(0, new_chat_name)
            st.session_state.current_chat = new_chat_name
            st.rerun()
        
        st.divider()
        st.write("🕒 **Lịch sử gần đây**")
        
        for i, chat in enumerate(st.session_state.chat_history):
            col_name, col_action = st.columns([0.85, 0.15], vertical_alignment="center")
            with col_name:
                is_active = (chat == st.session_state.current_chat)
                if st.button(chat[:20], key=f"btn_chat_{i}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state.current_chat = chat
                    st.rerun()
            with col_action:
                with st.popover("⋮"):
                    if st.button("🗑️ Xóa", key=f"delete_{i}", use_container_width=True):
                        st.session_state.chat_history.pop(i)
                        st.rerun()
        
        st.divider()
        with st.expander("⚙️ Cài đặt Model & Chunking", expanded=True):
            st.slider("Chunk Size", 100, 1000, 200)
            st.toggle("📊 Báo cáo & So sánh độ chính xác", value=False, key="show_report_toggle")

def create_chat_column(title, engine_name):
    st.subheader(f"{title}")
    with st.container(height=450, border=True):
        for i in range(3):
            with st.chat_message("user"): st.write(f"Câu hỏi mẫu cho {engine_name}...")
            with st.chat_message("assistant"): st.write(f"Trả lời từ {engine_name}: Nội dung phân tích từ tài liệu...")

def create_right_side_bar(col):
    with col:
        st.subheader("📂 Nguồn")
        
        # Khởi tạo trạng thái chọn file nếu chưa có
        if "selected_docs" not in st.session_state:
            st.session_state.selected_docs = {doc: True for doc in danh_sach_tai_lieu}

        with st.container(height=450, border=True):
            # CHẾ ĐỘ 1: ĐANG XEM CHI TIẾT FILE
            if st.session_state.viewing_doc:
                if st.button("↖ Quay lại danh sách", use_container_width=True):
                    st.session_state.viewing_doc = None
                    st.rerun()
                
                st.divider()
                st.subheader(f"📄 {st.session_state.viewing_doc}")
                st.caption("Nội dung tóm tắt hoặc chi tiết của file sẽ hiển thị tại đây để bạn kiểm tra.")
                st.info("Hệ thống RAG sẽ chỉ truy xuất dữ liệu từ các file được tích chọn ở màn hình danh sách.")

            # CHẾ ĐỘ 2: DANH SÁCH FILE CÓ CHECKBOX ĐỂ FILTER
            else:
                # Nút chọn tất cả / bỏ chọn tất cả
                c_text, c_toggle = st.columns([0.7, 0.3], vertical_alignment="center")
                with c_text:
                    st.write("**Chọn tất cả nguồn**")
                with c_toggle:
                    # Logic chọn tất cả nhanh
                    all_selected = all(st.session_state.selected_docs.values())
                    if st.checkbox("All", value=all_selected, label_visibility="collapsed", key="all_selector_checkbox"):
                        for doc in danh_sach_tai_lieu:
                            st.session_state.selected_docs[doc] = True
                    # Lưu ý: Trong thực tế bạn có thể cần logic phức tạp hơn để xử lý toggle All

                st.divider()

                # Hiển thị từng file kèm Checkbox
                for doc in danh_sach_tai_lieu:
                    # Chia 3 cột: Checkbox | Tên file | Nút xem
                    col_check, col_name = st.columns([0.15, 0.85], vertical_alignment="center")
                    
                    with col_check:
                        # Checkbox để filter nguồn cho RAG
                        st.session_state.selected_docs[doc] = st.checkbox(
                            f"Select {doc}", 
                            value=st.session_state.selected_docs.get(doc, True),
                            key=f"chk_{doc}",
                            label_visibility="collapsed"
                        )
                    
                    with col_name:
                        display_name = doc if len(doc) <= 20 else doc[:17] + "..."
                        # Nhấn vào tên file để xem chi tiết nội dung
                        if st.button(display_name, key=f"view_{doc}", help=f"Xem chi tiết {doc}", use_container_width=True):
                            st.session_state.viewing_doc = doc
                            st.rerun()
# --- 3. THIẾT LẬP LAYOUT CHÍNH ---
def main():
    create_side_bar()
    
    # Chia cột chính
    col_RAG, col_coRAG, col_right = st.columns([3, 3, 2], gap="medium")
    
    with col_RAG:
        create_chat_column("RAG 🔵", "RAG")
        
    with col_coRAG:
        create_chat_column("coRAG 🟠", "coRAG")
        
    create_right_side_bar(col_right)

    # Ô nhập liệu chung nằm dưới cùng
    st.chat_input("Nhập câu hỏi để so sánh hai hệ thống...")

    # KIỂM TRA TOGGLE ĐỂ HIỂN THỊ BÁO CÁO (Nằm ngoài các cột trên để dàn hàng ngang)
    if st.session_state.get("show_report_toggle"):
        display_comparison_report()

if __name__ == "__main__":
    main()