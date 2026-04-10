import define
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Tận dụng lại llm và embedder từ file rag_core.py của bạn
from rag_core import llm, embedder 

def get_corag_prompt():
    # Ép LLM phải suy nghĩ trong thẻ <think> trước khi trả lời
    prompt_text = """Sử dụng ngữ cảnh sau đây để trả lời câu hỏi. 
    BẠN LÀ MỘT CHUYÊN GIA PHÂN TÍCH. BẠN BẮT BUỘC PHẢI LÀM THEO 2 BƯỚC:
    
    1. Suy nghĩ: Phân tích ngữ cảnh và liên kết thông tin. Viết toàn bộ quá trình suy nghĩ của bạn vào giữa thẻ <think> và </think>.
    2. Trả lời: Đưa ra câu trả lời cuối cùng BẮT BUỘC bằng tiếng Việt, ngắn gọn và chính xác, đặt trong thẻ <answer> và </answer>.
    
    Ngữ cảnh: {context}
    Câu hỏi: {question}
    """
    return prompt_text

def generate_corag_stream(user_input, session_id, selected_files=None):
    save_path = define.document_vector_path + session_id
    vectorstores = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
    
    search_kwargs = {"k": 3}
    if selected_files and len(selected_files) > 0:
        search_kwargs["filter"] = lambda metadata: metadata.get("file_name") in selected_files

    retriever = vectorstores.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )

    prompt = ChatPromptTemplate.from_template(get_corag_prompt())

    # RAG Chain tiêu chuẩn
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # QUAN TRỌNG: Thay vì dùng .invoke(), ta dùng .stream()
    # Hàm này sẽ trả về một generator (yield từng chunk text)
    return rag_chain.stream(user_input)