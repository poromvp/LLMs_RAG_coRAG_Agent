import streamlit as st
import sidebar as sb
import rag_chat as rag_chat
import co_rag_chat as co_rag_chat
import explorer as explorer
import analize as analize



if __name__ == "__main__":
    sb.sidebar()
    col_rag, col_corag, ex = st.columns([3,3,2])
    with col_rag:
        rag_chat.rag_chat()
    with col_corag:
        co_rag_chat.co_rag_chat()
    with ex:
        explorer.explorer()
    