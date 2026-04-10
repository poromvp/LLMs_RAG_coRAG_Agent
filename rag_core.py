import os
import define
from langchain_community.document_loaders import PDFPlumberLoader, DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import DistanceStrategy
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from pprint import pprint
# ==========EMBEDDING==========
embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# ==========LLM==========
llm = Ollama(
    model="qwen2.5:3b",
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1
)

def process_and_save_documents(temp_folder_path, session_id): 
    # temp_folder_path: Bây giờ là một thư mục tạm CHỈ CHỨA NHỮNG FILE VỪA GỬI LÊN.
    
    # 1. LOAD DATA: Dùng DirectoryLoader kết hợp UnstructuredFileLoader
    # UnstructuredFileLoader tự động nhận diện cả .pdf, .docx, .txt... vô cùng mạnh mẽ!
    loader = DirectoryLoader(
        path=temp_folder_path,
        glob="**/*.*", # Chấp nhận mọi định dạng
        loader_cls=UnstructuredFileLoader,
        show_progress=True,
        use_multithreading=True # Bật đa luồng chạy max tốc độ
    )
    docs = loader.load()

    for doc in docs:
        # doc.metadata['source'] thường có dạng: "/tmp/folder/file_cua_toi.pdf"
        # os.path.basename sẽ cắt lấy đúng "file_cua_toi.pdf"
        file_name = os.path.basename(doc.metadata.get('source', ''))
        doc.metadata['file_name'] = file_name

    # 2. CHUNKING
    MARKDOWN_SEPARATORS = ["\n#{1,6}", "```\n", "\n\\*\\*\\*+\n", "\n---+\n", "\n---+\n", "\n\n", "\n", " ", ""]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=MARKDOWN_SEPARATORS,
        add_start_index=True,
        strip_whitespace=True
    )
    documents = text_splitter.split_documents(docs)
    # 3. VECTORSTORE (Vẫn duy trì khả năng nhớ dai như cũ)
    save_path = define.document_vector_path + session_id
    os.makedirs(save_path, exist_ok=True)
    
    index_file = os.path.join(save_path, "index.faiss")
    if os.path.exists(index_file):
        vectorstores = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
        vectorstores.add_documents(documents)
    else:
        vectorstores = FAISS.from_documents(documents=documents, embedding=embedder)
    vectorstores.save_local(save_path)
    return True

# ==========PROMPT==========
# Nhận diện tiếng việt để trả lời bằng tiếng việt
def get_dynamic_prompt(user_input):
    # Auto-detect language
    vietnamese_chars = 'àáãạảăằắẵặẳâầấẫậẩèéẽẹẻêềếễệểìíĩịỉòóõọỏôồốỗộổơờớỡợởùúũụủưừứữựửỳýỹỵỷđ'
    is_vietnamese = any(char in user_input.lower() for char in vietnamese_chars)

    if is_vietnamese:
        prompt_text = """Sử dụng ngữ cảnh sau đây để trả lời câu hỏi.
        Nếu bạn không biết, chỉ cần nói là bạn không biết.
        Trả lời ngắn gọn (3-4 câu) BẮT BUỘC bằng tiếng Việt.
        
        Ngữ cảnh: {context}
        Câu hỏi: {question}
        Trả lời:"""
    else:
        prompt_text = """Use the following context to answer the question.
        If you don't know the answer, just say you don't know.
        Keep answer concise (3-4 sentences).
        
        Context: {context}
        Question: {question}
        Answer:"""
    return prompt_text

def generate_answer(user_input, session_id, selected_files=None):
    save_path = define.document_vector_path + session_id

    vectorstores = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
    
    search_kwargs = {"k": 3}

    if selected_files and len(selected_files) > 0:
        # FAISS sẽ tự động kiểm tra xem thẻ 'file_name' của đoạn text đó có nằm trong danh sách không
        search_kwargs["filter"] = lambda metadata: metadata.get("file_name") in selected_files

    # ==========RETRIEVER==========
    retriever = vectorstores.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )

    # ==========PROMPT==========
    prompt_text = get_dynamic_prompt(user_input)
    prompt = ChatPromptTemplate.from_template(prompt_text)


    # ==========RAG CHAIN==========
    rag_chain = (
        {"context": retriever , "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # ==========INVOKE==========
    return rag_chain.invoke(user_input)

def get_corag_prompt():
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
    
    # Load lại vector store
    vectorstores = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
    
    search_kwargs = {"k": 3}
    if selected_files and len(selected_files) > 0:
        search_kwargs["filter"] = lambda metadata: metadata.get("file_name") in selected_files

    retriever = vectorstores.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )

    prompt = ChatPromptTemplate.from_template(get_corag_prompt())

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Dùng stream() thay vì invoke()
    return rag_chain.stream(user_input)