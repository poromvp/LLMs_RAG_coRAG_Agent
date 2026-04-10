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
# ==========LOAD DATA==========
loader = DirectoryLoader(
    path="./data",
    glob="**/*.pdf",
    loader_cls=PDFPlumberLoader,
    show_progress=True,
    use_multithreading=True
)

docs = loader.load()

# ==========CHUNKING==========
MARKDOWN_SEPARATORS = [
    "\n#{1,6}",
    "```\n",
    "\n\\*\\*\\*+\n",
    "\n---+\n",
    "\n---+\n",
    "\n\n",
    "\n",
    " ",
    ""
]

text_slpitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,

    separators=MARKDOWN_SEPARATORS,
    add_start_index=True,
    strip_whitespace=True
)

documents = text_slpitter.split_documents(docs)

# ==========EMBEDDING==========
embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# ==========VECTORSTORE==========
vectorstores = FAISS.from_documents(
    documents=documents,
    embedding=embedder
)

# ==========RETRIEVER==========
retriever = vectorstores.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ==========LLM==========
llm = Ollama(
    model="qwen2.5:3b",
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1
)

# ==========PROMPT==========
# Auto-detect language and respond accordingly
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


user_input = input("Bạn muốn hỏi gì?: ")

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
answer = rag_chain.invoke(user_input)
print(answer)
